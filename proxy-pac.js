function FindProxyForURL (url, host) {
	if (shExpMatch(url, "*webappsecurity.com*")) return 'HTTP localhost:8156'
    return 'DIRECT';
}
