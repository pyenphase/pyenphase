"""Pyenphase SSL helper"""

import contextlib
import ssl


def create_no_verify_ssl_context() -> ssl.SSLContext:
    """
    Return an SSL context that does not verify the server certificate.

    This is a copy of aiohttp's create_default_context() function, with the
    ssl verify turned off and old SSL versions enabled.

    https://github.com/aio-libs/aiohttp/blob/33953f110e97eecc707e1402daa8d543f38a189b/aiohttp/connector.py#L911

    :return: SSLcontext with ssl verify turned off.
    """
    sslcontext = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    sslcontext.check_hostname = False
    sslcontext.verify_mode = ssl.CERT_NONE
    # Allow all ciphers rather than only Python 3.10 default
    sslcontext.set_ciphers("DEFAULT")
    with contextlib.suppress(AttributeError):
        # This only works for OpenSSL >= 1.0.0
        sslcontext.options |= ssl.OP_NO_COMPRESSION
    sslcontext.set_default_verify_paths()
    return sslcontext


#: Alias for :any:`create_no_verify_ssl_context`
#:
#: .. code-block:: python
#:
#:     import httpx
#:     from pyenphase.ssl import NO_VERIFY_SSL_CONTEXT
#:
#:     client = httpx.AsyncClient(verify=NO_VERIFY_SSL_CONTEXT)
NO_VERIFY_SSL_CONTEXT = create_no_verify_ssl_context()


def create_default_ssl_context() -> ssl.SSLContext:
    """Create httpx client with default SSL context."""
    return ssl.create_default_context()


#: Alias for :any:`create_default_ssl_context`
#:
#: .. code-block:: python
#:
#:    import httpx
#:    from pyenphase.ssl import SSL_CONTEXT
#:
#:    async with httpx.AsyncClient(verify=SSL_CONTEXT) as client:
#:        response = await client.post(url, json=json, data=data)
#:
SSL_CONTEXT = create_default_ssl_context()
