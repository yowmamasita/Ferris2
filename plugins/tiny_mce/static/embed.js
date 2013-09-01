$(function() {
    $('textarea.flag_tinymce_true, textarea.tinymce').tinymce({
        script_url : '/plugins/tiny_mce/tinymce/tinymce.min.js',
        keep_styles: true,
        paste_remove_styles: false,
        paste_remove_spans: false,
        paste_strip_class_attributes: 'none',
        paste_text_use_dialog: true,
        relative_urls : false,
        apply_source_formatting: false,
        plugins: [
            "advlist autolink lists link image preview hr anchor pagebreak",
            "searchreplace wordcount visualblocks visualchars code fullscreen",
            "insertdatetime media nonbreaking save table contextmenu",
            "template paste"],
        file_browser_callback : tinymce_file_browser
    });
});
