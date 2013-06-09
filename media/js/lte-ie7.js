/* Load this script using conditional IE comments if you need to support IE 7 and IE 6. */

window.onload = function() {
	function addIcon(el, entity) {
		var html = el.innerHTML;
		el.innerHTML = '<span style="font-family: \'icomoon\'">' + entity + '</span>' + html;
	}
	var icons = {
			'icon-tab' : '&#xe000;',
			'icon-drop-arrow' : '&#xe005;',
			'icon-printer' : '&#xe00d;',
			'icon-drive' : '&#xe00e;',
			'icon-users' : '&#xe00f;',
			'icon-cancel' : '&#xe010;',
			'icon-filter' : '&#xe011;',
			'icon-facebook' : '&#xe012;',
			'icon-mail' : '&#xe014;',
			'icon-twitter' : '&#xe015;',
			'icon-tags' : '&#xe016;',
			'icon-tag' : '&#xe017;',
			'icon-popup' : '&#xe001;'
		},
		els = document.getElementsByTagName('*'),
		i, attr, html, c, el;
	for (i = 0; ; i += 1) {
		el = els[i];
		if(!el) {
			break;
		}
		attr = el.getAttribute('data-icon');
		if (attr) {
			addIcon(el, attr);
		}
		c = el.className;
		c = c.match(/icon-[^\s'"]+/);
		if (c && icons[c[0]]) {
			addIcon(el, icons[c[0]]);
		}
	}
};