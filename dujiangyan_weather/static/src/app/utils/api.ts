/**
 * 获取 Django CSRF Token（从 cookie 中读取）。
 * 用于 POST 请求的 X-CSRFToken 请求头。
 */
function getCsrfToken(): string {
  const name = 'csrftoken';
  if (document.cookie.includes(name)) {
    const cookies = document.cookie.split(';');
    for (const cookie of cookies) {
      const trimmed = cookie.trim();
      if (trimmed.startsWith(`${name}=`)) {
        return decodeURIComponent(trimmed.substring(name.length + 1));
      }
    }
  }
  return '';
}

/**
 * 封装 fetch，自动为 POST/PUT/PATCH/DELETE 添加 CSRF Token。
 * 用法与原生 fetch 相同。
 */
export async function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const method = (options.method || 'GET').toUpperCase();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  // 对于修改类请求，自动添加 CSRF Token
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      headers['X-CSRFToken'] = csrfToken;
    }
    // 若未设置 Content-Type 且不是 FormData，默认 JSON
    if (!headers['Content-Type'] && !(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }
  }

  return fetch(url, { ...options, method, headers });
}
