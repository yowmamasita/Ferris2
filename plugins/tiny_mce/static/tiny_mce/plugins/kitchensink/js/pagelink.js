tinyMCEPopup.requireLangPack();

var PageLinkDialog = {
	init : function(ed) {
		this.editor = ed;
        var f = document.forms[0];
        
        // if a page is already selected, set the value to that.
        elm = ed.selection.getNode();
        if( elm.tagName != 'A' ) ed.dom.getParent(elm, 'A');
		v = ed.dom.getAttrib(elm, 'href');

		if (v) {
            if( v.indexOf('/pages/view/') != -1 ){
                f.pageSelect.value = v.substring(12, v.length);
            }
		}
	},

	update : function() {
		var ed = this.editor, elm;
        var page_href = document.forms[0].pageSelect.value;

		tinyMCEPopup.restoreSelection();

		ed.execCommand('mceInsertLink', 0, '/pages/view/' + page_href);

		tinyMCEPopup.close();
	}
};

tinyMCEPopup.onInit.add(PageLinkDialog.init, PageLinkDialog);
