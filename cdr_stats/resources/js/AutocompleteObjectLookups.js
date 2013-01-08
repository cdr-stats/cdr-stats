function showAutocompletePopup(triggeringLink) {
    var name = triggeringLink.id.replace(/^add_/, '');
    name = id_to_windowname(name);
    href = triggeringLink.href
    if (href.indexOf('?') == -1) {
        href += '?_popup=2';
    } else {
        href  += '&_popup=2';
    }
    var win = window.open(href, name, 'height=500,width=800,resizable=yes,scrollbars=yes');
    win.focus();
    return false;
}

function dismissAutocompletePopup(win, newId, newRepr) {

    newId = html_unescape(newId);
    newRepr = html_unescape(newRepr);
    var name = windowname_to_id(win.name);
	var calback = 'addItem_' + name;
	// --- add result ---
	try{
	
		eval(calback+'("'+newId+'","'+newRepr+'")');
		win.close();
	}catch(err){
		//Handle errors here
		// try default callback
		dismissAddAnotherPopup(win, newId, newRepr);
	}	
}
