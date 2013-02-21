(function() {
    
    tinymce.create('oqq.plugins.KitchenSink', {
        
        /* Variables used through the plugin */
        url : '',
        ed: null,
        
        /**
		 * Initializes the plugin, this will be executed after the plugin has been created.
		 * This call is done before the editor instance has finished it's initialization so use the onInit event
		 * of the editor instance to intercept that event.
		 *
		 * @param {tinymce.Editor} ed Editor instance that the plugin is initialized in.
		 * @param {string} url Absolute URL to where the plugin is located.
		 */
		init : function(ed, url) {
            this.ed = ed;
            this.url = url;
            
            // On initialization, hide the second toolbar
            ed.onInit.add( function(ed){
                $('.mceToolbarRow2').hide();
            });
            
			// Register the command so that it can be invoked by using tinyMCE.activeEditor.execCommand('mceExample');
			ed.addCommand('mceToggleKitchenSink', function() {
                $('.mceToolbarRow2').toggle();
			});

			// Register the button
			ed.addButton('kitchensink', {
				title : 'Show/Hide Kitchen Sink',
				cmd : 'mceToggleKitchenSink',
				image : url + '/img/toolbars.gif'
			});

		},

        
        /**
		 * Returns information about the plugin as a name/value array.
		 * The current keys are longname, author, authorurl, infourl and version.
		 *
		 * @return {Object} Name/value array containing information about the plugin.
		 */
		getInfo : function() {
			return {
				longname : 'Kitchen Sink Plugin',
				author : 'Jon Parrott',
				version : "1.0"
			};
		}
        
    });
    
    // Register plugin
	tinymce.PluginManager.add('kitchensink', oqq.plugins.KitchenSink);

})();