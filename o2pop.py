#
# o2pop.py
#
# Copyright (c) 2020-2021 MURATA Yasuhisa
# Copyright (c) 2022 yamahubuki, ACT Laboratory
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
#

import constants

import asyncio
import ssl
import sys
import socket
import argparse
import traceback
import base64
from google.auth import transport

import globalVars
import googleOAuthUtil

from google.auth.transport.requests import Request
from logging import getLogger

__version__ = '3.0.0'

PROG = 'o2pop'

LOCAL_HOST = '127.0.0.1'

SCOPES = ['https://mail.google.com/']
REMOTE_POP_HOST = 'pop.gmail.com'
REMOTE_POP_PORT = 995
REMOTE_SMTP_HOST = 'smtp.gmail.com'
REMOTE_SMTP_PORT = 465

LOCAL_POP_PORT = 8110
LOCAL_SMTP_PORT = 8025

MS_MODE = 1

log = getLogger("%s.%s" % (constants.LOG_PREFIX,"o2pop"))


def print2(label, s):
    log.debug(f'{label} {s}')

async def pop_init(local_reader, local_writer, remote_reader, remote_writer, verbose=None):
    # <<< +OK ... ready
    if remote_reader.at_eof():
        return 1
    s = await remote_reader.readline()
    if verbose:
        print2("<<<", s)
    local_writer.write(s)
    await local_writer.drain()

    # USER name / QUIT / CAPA
    if local_reader.at_eof():
        return 1
    s = await local_reader.readline()
    if verbose:
        print2(">>>", s)

    cmd = s.lower().rstrip()
    if cmd != b'quit' and cmd != b'capa' and (not cmd.startswith(b'user ')):
        s = b'-ERR malformed command\r\n'
        if verbose:
            print2("<<!", s)
        local_writer.write(s)
        await local_writer.drain()

        # QUIT / CAPA / USER name
        if local_reader.at_eof():
            return 1
        s = await local_reader.readline()
        if verbose:
           print2(">>>", s)
        cmd = s.lower().rstrip()

    if cmd == b'capa':
        remote_writer.write(s)
        await remote_writer.drain()

        while not remote_reader.at_eof():
            s = await remote_reader.readline()
            if verbose:
                print2("<<<", s)
            if s.startswith(b'.'):
                break
        s = b'+OK Capability list follows\r\nUSER\r\nTOP\r\nUIDL\r\n.\r\n'
        if verbose:
            print2("<<!", s)
        local_writer.write(s)
        await local_writer.drain()

        # QUIT / USER name
        if local_reader.at_eof():
            return 1
        s = await local_reader.readline()
        if verbose:
            print2(">>>", s)
        cmd = s.lower().rstrip()

    if cmd.startswith(b'user '):
        t = s.split()
        if len(t) >= 2:
            user = t[1]
        else:
            user = b''
        if verbose: # debug
            print2('User:', user)

    if cmd == b'quit':
        remote_writer.write(s)
        await remote_writer.drain()
        if remote_reader.at_eof():
            return 1
        s = await remote_reader.readline()
        if verbose:
            print2("<<<", s)
        local_writer.write(s)
        await local_writer.drain()
        return 1

    s = b'+OK send PASS\r\n'
    if verbose:
        print2("<<!", s)
    local_writer.write(s)
    await local_writer.drain()

    # PASS string
    if local_reader.at_eof():
        return 1
    s = await local_reader.readline()
    if verbose:
        print2(">>>", s)

    # AUTH
    token = params.get_token(user.decode()).encode()

    auth_string = b'user=%b\1auth=Bearer %b\1\1' % (user, token)

    if params.mode == MS_MODE:
        s = b'AUTH XOAUTH2\r\n'
        if verbose:
            print2("!>>", s)
        remote_writer.write(s)
        await remote_writer.drain()

        # <<< b'+ '
        if remote_reader.at_eof():
            return 1
        s = await remote_reader.readline()
        if verbose:
            print2("<<<", s)
        
        s = base64.b64encode(auth_string) + b'\r\n'
    else:
        s = b'AUTH XOAUTH2 %b\r\n' % base64.b64encode(auth_string)

    if verbose:
        print2("!>>", s)

    remote_writer.write(s)
    await remote_writer.drain()

    # OK: <<< +OK Welcome.
    # NG: <<< + eyJzdGF0d...
    if remote_reader.at_eof():
        return 1
    s = await remote_reader.readline()
    if verbose:
        print2("<<<", s)
    
    if not s.startswith(b'+OK'):
        s = b'-ERR Bad login\r\n'
        if verbose:
            print2("<<!", s)
        local_writer.write(s)
        await local_writer.drain()
        return 1

    local_writer.write(s)
    await local_writer.drain()

    return 0

async def pipe(reader, writer, label=None):
    if label is None:
        while not reader.at_eof():
            writer.write(await reader.read(2048))
    else:
        while not reader.at_eof():
            s = await reader.readline()
            print2(label, s)
            writer.write(s)

async def handle_pop(local_reader, local_writer):
    try:
        ctx = ssl.create_default_context()
        if args.ca_file:
            ctx.load_verify_locations(cafile=args.ca_file)

        if args.verbose:
            log.info("Connect to " + params.remote_pop_host + ":" + str(params.remote_pop_port))

        remote_writer = None
        remote_reader, remote_writer = await asyncio.open_connection(
            params.remote_pop_host, params.remote_pop_port, ssl=ctx, limit = 32*1024*1024)

        res = await pop_init(local_reader, local_writer, remote_reader, remote_writer, args.verbose)
        if res > 0:
            return

        (label1, label2) = (None, None)
        if args.verbose:
            (label1, label2) = ('>>>', '<<<')
        pipe1 = pipe(local_reader, remote_writer, label1)
        pipe2 = pipe(remote_reader, local_writer, label2)

        await asyncio.gather(pipe1, pipe2)

    except Exception as ex:
        log.error(sys.exc_info()[0].__name__ + ":" + str(ex))
        log.error(traceback.format_exc())
        local_writer.write(b'-ERR\r\n')
        await local_writer.drain()

    finally:
        if remote_writer:
            remote_writer.close()
        local_writer.close()

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

async def smtp_init(local_reader, local_writer, remote_reader, remote_writer, start_tls_ctx=None, verbose=None):
    # <<< 220 ... Service ready
    if remote_reader.at_eof():
        return 1
    s = await remote_reader.readline()
    if verbose:
        print2("<<<", s)
    local_writer.write(s)
    await local_writer.drain()

    # EHLO / QUIT
    if local_reader.at_eof():
        return 1
    s = await local_reader.readline()
    if verbose:
        print2(">>>", s)

    cmd = s.lower().rstrip()
    if cmd == b'quit':
        remote_writer.write(s)
        await remote_writer.drain()
        if remote_reader.at_eof():
            return 1
        s = await remote_reader.readline()
        if verbose:
            print2("<<<", s)
        local_writer.write(s)
        await local_writer.drain()
        return 1

    if cmd.startswith(b'ehlo '):
        s = b'EHLO [%b]\r\n' % params.ip_addr.encode()
        if verbose:
            print2("!>>", s)
        remote_writer.write(s)
        await remote_writer.drain()

        while True:
            if remote_reader.at_eof():
                return 1
            s = await remote_reader.readline()
            if verbose:
                print2("<<<", s)
            local_writer.write(s)
            await local_writer.drain()
            if s[3:4] == b' ':
                break

    if start_tls_ctx:
        s = b'STARTTLS\r\n'
        if verbose:
            print2("!>>", s)
        remote_writer.write(s)
        await remote_writer.drain()

        if remote_reader.at_eof():
            return 1

        s = await remote_reader.readline()
        if verbose:
            print2("<<<", s)

        transport = remote_writer.transport
        protocol = transport.get_protocol()
        protocol._over_ssl = True
        loop = asyncio.get_event_loop()

        tls_transport = await loop.start_tls(transport, protocol, start_tls_ctx)
        remote_writer._transport = tls_transport
        remote_reader._transport = tls_transport

        if params.mode == MS_MODE:
            # EHLO
            s = b'EHLO [%b]\r\n' % params.ip_addr.encode()
            if verbose:
                print2("!>>", s)
            remote_writer.write(s)
            await remote_writer.drain()

            while True:
                if remote_reader.at_eof():
                    return 1
                s = await remote_reader.readline()
                if verbose:
                    print2("<<<", s)
                if s[3:4] == b' ':
                    break

    # MAIL FROM: / AUTH PLAIN / AUTH LOGIN / QUIT
    if local_reader.at_eof():
        return 1
    s = await local_reader.readline()
    if verbose:
       print2(">>>", s)

    mail_from_buff = b''

    cmd = s.lower().rstrip()
    if cmd == b'quit':
        remote_writer.write(s)
        await remote_writer.drain()
        if remote_reader.at_eof():
            return 1
        s = await remote_reader.readline()
        if verbose:
            print2("<<<", s)
        local_writer.write(s)
        await local_writer.drain()
        return 1

    if cmd.startswith(b'mail '):
        mail_from_buff = s
        t = s.split(b':', 1)
        if len(t) == 2:
            user = t[1].split()[0].strip(b'<>')
        else:
            user = b''
        if verbose: # debug
            log.info('User:' + user.decode())
    elif cmd.startswith(b'auth plain '):
        t = base64.b64decode(s[11:]).split(b'\0')
        if len(t) == 3:
            user = t[1]
        else:
            user = b''
        if verbose: # debug
            log.info('User:' + user.decode())
    elif cmd.startswith(b'auth plain'):
        s = b'334\r\n'
        if verbose:
            print2("<<!", s)
        local_writer.write(s)
        await local_writer.drain()
        if local_reader.at_eof():
            return 1
        s = await local_reader.readline()
        if verbose:
            print2(">>>", s)
        t = base64.b64decode(s).split(b'\0')
        if len(t) == 3:
            user = t[1]
        else:
            user = b''
        if verbose: # debug
            log.info('User:' + user.decode())
    elif cmd.startswith(b'auth login'):
        s = b'334 VXNlcm5hbWU6\r\n' # 'Username:'
        if verbose:
            print2("<<!", s)
        local_writer.write(s)
        await local_writer.drain()
        if local_reader.at_eof():
            return 1
        s = await local_reader.readline()
        if verbose:
            print2(">>>", s)
        user = base64.b64decode(s)
        if verbose: # debug
            log.info('User:' + user.decode())

        s = b'334 UGFzc3dvcmQ6\r\n' # 'Password:'
        if verbose:
            print2("<<!", s)
        local_writer.write(s)
        await local_writer.drain()
        if local_reader.at_eof():
            return 1
        s = await local_reader.readline()
        if verbose:
            print2(">>>", s)

    # AUTH
    token = params.get_token(user.decode()).encode()

    auth_string = b'user=%b\1auth=Bearer %b\1\1' % (user, token)
    s = b'AUTH XOAUTH2 %b\r\n' % base64.b64encode(auth_string)

    if verbose:
        print2("!>>", s)
    remote_writer.write(s)
    await remote_writer.drain()

    # OK: <<< 235 2.7.0 Accepted
    # NG: <<< 334 eyJzdGF0d...
    if remote_reader.at_eof():
        return 1
    s = await remote_reader.readline()
    if verbose:
        print2("<<<", s)

    parent = params.parent
    err = False

    if s.startswith(b'235'):
        # MAIL FROM:
        if mail_from_buff:
            s = mail_from_buff
            if verbose:
                print2("!>>", s)
            remote_writer.write(s)
            await remote_writer.drain()

            while True:
                if remote_reader.at_eof():
                    return 1
                s = await remote_reader.readline()
                if verbose:
                    print2("<<<", s)
                local_writer.write(s)
                await local_writer.drain()
                if s[3:4] == b' ':
                    break

            if not s.startswith(b'250'):
                err = True
        else:
            local_writer.write(s)
            await local_writer.drain()
    else:
        if s.startswith(b'334'):
            s = b'\r\n'
            if verbose:
                print2("!>>", s)
            remote_writer.write(s)
            await remote_writer.drain()

            while True:
                if remote_reader.at_eof():
                    return 1
                s = await remote_reader.readline()
                if verbose:
                    print2("<<<", s)
                if s[3:4] == b' ':
                    break

        s = b'535 Authentication failed\r\n'
        if verbose:
            print2("<<!", s)
        local_writer.write(s)
        await local_writer.drain()

        err = True

    if err:
        s = b'QUIT\r\n'
        if verbose:
            print2("!>>", s)
        remote_writer.write(s)
        await remote_writer.drain()
        if remote_reader.at_eof():
            return 1
        s = await remote_reader.readline()
        if verbose:
            print2("<<<", s)

        return 1

    if not params.parent:
        return 0

    rcpt_count = 0

    # MAIL FROM: / RCPT TO: / DATA
    while True:
        if local_reader.at_eof():
            return 1
        s = await local_reader.readline()
        if verbose:
            print2(">>>", s)

        cmd = s.lower().rstrip()
        if cmd == b'data':
            break

        mail_or_rcpt = False
        if cmd.startswith(b'mail '):
            mail_or_rcpt = True
            t = s.split(b':', 1)
            if len(t) == 2:
                env_from = t[1].split()[0].strip(b'<>')
        elif cmd.startswith(b'rcpt '):
            mail_or_rcpt = True
            rcpt_count += 1

        remote_writer.write(s)
        await remote_writer.drain()

        while True:
            if remote_reader.at_eof():
                return 1
            s = await remote_reader.readline()
            if verbose:
                print2("<<<", s)
            local_writer.write(s)
            await local_writer.drain()
            if s[3:4] == b' ':
                break

        if mail_or_rcpt:
            if not s.startswith(b'250'):
                err = True
                break
        else:
            return 1

    if err:
        s = b'QUIT\r\n'
        if verbose:
            print2("!>>", s)
        remote_writer.write(s)
        await remote_writer.drain()
        if remote_reader.at_eof():
            return 1
        s = await remote_reader.readline()
        if verbose:
            print2("<<<", s)
        return 1

    s = b'354 Start mail input; end with <CRLF>.<CRLF>\r\n'
    if verbose:
        print2("<<!", s)
    local_writer.write(s)
    await local_writer.drain()

    data = []
    while True:
        if local_reader.at_eof():
            return 1
        s = await local_reader.readline()
        if verbose:
            print2(">>>", s)
        data.append(s)
        if s == b'.\r\n':
            break

    s = b'DATA\r\n'
    if verbose:
        print2("!>>", s)
    remote_writer.write(s)
    await remote_writer.drain()
    if remote_reader.at_eof():
        return 1
    s = await remote_reader.readline()
    if verbose:
        print2("<<<", s)

    for s in data:
        if verbose:
            print2("!>>", s)
        remote_writer.write(s)
        await remote_writer.drain()
    if remote_reader.at_eof():
        return 1
    s = await remote_reader.readline()
    if verbose:
        print2("<<<", s)
    local_writer.write(s)
    await local_writer.drain()

    # QUIT

    if local_reader.at_eof():
        return 1
    s = await local_reader.readline()
    if verbose:
        print2(">>>", s)
    cmd = s.lower().rstrip()

    err = False
    if cmd != b'quit':
        err = True
        s = b'QUIT\r\n'
        if verbose:
            print2("!>>", s)
    remote_writer.write(s)
    await remote_writer.drain()
    if remote_reader.at_eof():
        return 1
    s = await remote_reader.readline()
    if verbose:
        print2("<<<", s)
    if err:
        return 1
    local_writer.write(s)
    await local_writer.drain()
    return 1

async def handle_smtp(local_reader, local_writer):
    try:
        ctx = ssl.create_default_context()
        if args.ca_file:
            ctx.load_verify_locations(cafile=args.ca_file)
        
        if params.remote_smtp_port == 587:
            start_tls_ctx = ctx
            ctx = None
        else:
            start_tls_ctx = None

        if args.verbose:
            log.info("Connect to " + params.remote_smtp_host + ":" + str(params.remote_smtp_port))

        remote_writer = None
        remote_reader, remote_writer = await asyncio.open_connection(
            params.remote_smtp_host, params.remote_smtp_port, ssl=ctx, limit = 32*1024*1024)

        res = await smtp_init(local_reader, local_writer, remote_reader, remote_writer, start_tls_ctx=start_tls_ctx, verbose=args.verbose)
        if res > 0:
            return

        (label1, label2) = (None, None)
        if args.verbose:
            (label1, label2) = ('>>>', '<<<')
        pipe1 = pipe(local_reader, remote_writer, label1)
        pipe2 = pipe(remote_reader, local_writer, label2)

        await asyncio.gather(pipe1, pipe2)

    except Exception as ex:
        log.error(sys.exc_info()[0].__name__ + ":" + str(ex))
        s = b'451 Requested action aborted\r\n'
        if args.verbose:
            print2("<<<", s)
        local_writer.write(s)
        await local_writer.drain()

    finally:
        if remote_writer:
            remote_writer.close()
        local_writer.close()

async def start_server(handle, host, port, name):
    server = await asyncio.start_server(handle, host, port)
    addr = server.sockets[0].getsockname()
    if args.verbose:
        log.info(f'Serving on {addr}: {name}')
    async with server:
        await server.serve_forever()

async def main(parent=None):
    loop = asyncio.get_running_loop()

    if not args.no_pop:
        pop_server = start_server(handle_pop, LOCAL_HOST, args.pop_port, 'pop')
    if not args.no_smtp:
        if args.verbose:
            log.info('local ip:' + params.ip_addr)
        smtp_server = start_server(handle_smtp, LOCAL_HOST, args.smtp_port, 'smtp')
    
    if parent is None:
        if args.no_pop:
            await smtp_server
        elif args.no_smtp:
            await pop_server
        else:
            await asyncio.gather(pop_server, smtp_server)
    else:
        if args.no_pop:
            task = asyncio.create_task(smtp_server)
        elif args.no_smtp:
            task = asyncio.create_task(pop_server)
        else:
            task = asyncio.gather(smtp_server, pop_server)

        globalVars.loop = loop
        globalVars.task = task

        try:
            await asyncio.gather(task)
        except asyncio.CancelledError:
            pass

def task_cancel(loop, task):
    loop.call_soon_threadsafe(task.cancel)

def run_main(coro):
    if args.verbose: # debug
        log.info('=== Start ===')
    asyncio.run(coro)
    if args.verbose: # debug
        log.info('=== Stop ===')

def parse_hostport(s, default_port=None):
    r = s.rsplit(":", 1)
    if len(r) == 1:
        port = default_port
    else:
        try:
            port = int(r[1])
        except ValueError:
            port = default_port
    return (r[0], port)

class Params:
    def __init__(self):
        self.parent = None
        self.ip_addr = None
        self.mode = None
        self.reset()

    def reset(self, parent=None):
        self.client_id = constants.GOOGLE_CLIENT_ID
        self.client_secret = constants.GOOGLE_CLIENT_SECRET_STR
        self.remote_pop_host = REMOTE_POP_HOST
        self.remote_pop_port = REMOTE_POP_PORT
        self.remote_smtp_host = REMOTE_SMTP_HOST
        self.remote_smtp_port = REMOTE_SMTP_PORT

    def get_token(self, user, login_hint=None):
        if user.startswith("recent:"):
            user = user[7:]
        log.debug("get token:"+user)
        creds = googleOAuthUtil.get(user, True)
        return creds.token

parser = argparse.ArgumentParser(prog=PROG)
parser.add_argument("--version", help="show version and exit",
    action="store_true")
parser.add_argument("-v", "--verbose", help="increase output verbosity",
    action="store_true")

group = parser.add_mutually_exclusive_group()
group.add_argument("--no_smtp", help="disable smtp proxy", action="store_true")
group.add_argument("--no_pop", help="disable pop proxy", action="store_true")
parser.add_argument("--smtp_port", type=int, default=LOCAL_SMTP_PORT, help="smtp listen port (default: %(default)s)")
parser.add_argument("--pop_port", type=int, default=LOCAL_POP_PORT, help="pop listen port (default: %(default)s)")
parser.add_argument("--ca_file", help="CA file")

args = parser.parse_args()
params = Params()


args.verbose = True

if not args.no_smtp:
    params.ip_addr = get_ip()

if __name__ == '__main__':
    if args.version:
        print(PROG, __version__)
        sys.exit()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
