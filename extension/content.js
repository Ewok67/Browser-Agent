(function() {
  const url = new URL(window.location.href);
  let query = null;
  const h = url.hostname;
  if (h.includes('google.')) query = url.searchParams.get('q');
  else if (h.includes('bing.com')) query = url.searchParams.get('q');
  else if (h.includes('duckduckgo.com')) query = url.searchParams.get('q');
  else if (h.includes('search.brave.com')) query = url.searchParams.get('q');
  else if (h.includes('yahoo.com')) query = url.searchParams.get('p');
  else if (h.includes('baidu.com')) query = url.searchParams.get('wd');

  if (query) {
    chrome.runtime.sendMessage({ type: 'CHECK_QUERY', query });
  }
})();
