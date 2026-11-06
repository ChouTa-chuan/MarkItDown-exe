"""保留系統 proxy／CA 的 HTTPS 傳輸，重新導向亦先檢查應用程式來源政策。"""
import urllib.request

from .catalog import MAX_CATALOG_BYTES, CatalogError


class ApprovedRedirects(urllib.request.HTTPRedirectHandler):
    def __init__(self, policy):
        self.policy = policy

    def redirect_request(self, request, response, code, message, headers, new_url):
        self.policy.check_url(new_url)
        redirected = super().redirect_request(request, response, code, message, headers, new_url)
        if redirected is not None and self.policy_origin(request.full_url) != self.policy_origin(new_url):
            # 跨核准 origin 的重新導向重新下載；不把舊位置的續傳條件帶給新位置。
            redirected.remove_header('Range')
            redirected.remove_header('If-range')
        return redirected

    def policy_origin(self, url):
        from .catalog import source_origin
        return source_origin(url)


def opener_for(policy):
    return urllib.request.build_opener(ApprovedRedirects(policy)).open


def fetch_catalog(url, verifier, *, opener=None, checkpoint=lambda: None):
    verifier.policy.check_url(url)
    checkpoint()
    request = urllib.request.Request(url, headers={'Accept-Encoding': 'identity'})
    with (opener or opener_for(verifier.policy))(request, timeout=10) as response:
        verifier.policy.check_url(response.geturl())
        if response.status != 200 or response.headers.get('Content-Encoding', 'identity') != 'identity':
            raise CatalogError('目錄 HTTP 回應不符。')
        blocks = []
        count = 0
        while True:
            checkpoint()
            block = response.read(min(65536, MAX_CATALOG_BYTES + 1 - count))
            if not block:
                break
            count += len(block)
            if count > MAX_CATALOG_BYTES:
                raise CatalogError('目錄下載超過大小限制。')
            blocks.append(block)
    checkpoint()
    return verifier.load(b''.join(blocks))
