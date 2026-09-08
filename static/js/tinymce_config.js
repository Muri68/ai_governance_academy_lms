// TinyMCE Configuration for Blog
document.addEventListener('DOMContentLoaded', function() {
    if (typeof tinymce !== 'undefined') {
        tinymce.init({
            selector: '.tinymce-editor',
            height: 500,
            menubar: true,
            plugins: [
                'advlist', 'autolink', 'lists', 'link', 'image', 'charmap', 'preview',
                'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
                'insertdatetime', 'media', 'table', 'help', 'wordcount',
                'codesample', 'emoticons', 'template', 'paste', 'autoresize'
            ],
            toolbar: 'undo redo | blocks | ' +
                'bold italic underline strikethrough | ' +
                'forecolor backcolor | ' +
                'alignleft aligncenter alignright alignjustify | ' +
                'bullist numlist outdent indent | ' +
                'link image media table | ' +
                'codesample emoticons | ' +
                'removeformat | code | help',
            content_style: 'body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 14px; color: #1e293b; line-height: 1.6; } ' +
                'pre { background: #1e293b; color: #e2e8f0; padding: 16px; border-radius: 8px; } ' +
                'code { background: #f1f5f9; color: #e11d48; padding: 2px 6px; border-radius: 4px; } ' +
                'img { max-width: 100%; height: auto; } ' +
                'h1, h2, h3, h4, h5, h6 { color: #0f172a; margin-top: 1.5em; margin-bottom: 0.5em; } ' +
                'p { margin-bottom: 1em; } ' +
                'a { color: #ad7a49; } ' +
                'table { border-collapse: collapse; width: 100%; margin-bottom: 1em; } ' +
                'table td, table th { border: 1px solid #ddd; padding: 8px; } ' +
                'table tr:nth-child(even) { background-color: #f2f2f2; } ' +
                'table tr:hover { background-color: #ddd; } ' +
                'table th { padding-top: 12px; padding-bottom: 12px; text-align: left; background-color: #ad7a49; color: white; }',
            codesample_languages: [
                { text: 'HTML/XML', value: 'markup' },
                { text: 'JavaScript', value: 'javascript' },
                { text: 'Python', value: 'python' },
                { text: 'CSS', value: 'css' },
                { text: 'PHP', value: 'php' },
                { text: 'Java', value: 'java' },
                { text: 'SQL', value: 'sql' },
                { text: 'Bash', value: 'bash' },
                { text: 'JSON', value: 'json' },
                { text: 'Markdown', value: 'markdown' }
            ],
            image_advtab: true,
            image_caption: true,
            image_title: true,
            automatic_uploads: true,
            file_picker_types: 'image',
            file_picker_callback: function(callback, value, meta) {
                // Custom file picker for image upload
                const input = document.createElement('input');
                input.setAttribute('type', 'file');
                input.setAttribute('accept', 'image/*');
                
                input.onchange = function() {
                    const file = this.files[0];
                    const reader = new FileReader();
                    
                    reader.onload = function() {
                        const id = 'blobid' + (new Date()).getTime();
                        const blobCache = tinymce.activeEditor.editorUpload.blobCache;
                        const base64 = reader.result.split(',')[1];
                        const blobInfo = blobCache.create(id, file, base64);
                        blobCache.add(blobInfo);
                        
                        callback(blobInfo.blobUri(), { title: file.name });
                    };
                    
                    reader.readAsDataURL(file);
                };
                
                input.click();
            },
            paste_data_images: true,
            media_dimensions: false,
            media_poster: false,
            media_alt_source: true,
            media_live_embeds: true,
            table_appearance_options: true,
            table_grid: true,
            table_tab_navigation: true,
            table_default_attributes: {
                border: '1'
            },
            table_default_styles: {
                'border-collapse': 'collapse',
                'width': '100%'
            },
            table_class_list: [
                { title: 'None', value: '' },
                { title: 'Bordered', value: 'table-bordered' },
                { title: 'Striped', value: 'table-striped' }
            ],
            quickbars_selection_toolbar: 'bold italic | quicklink h2 h3 blockquote quickimage quicktable',
            quickbars_insert_toolbar: false,
            contextmenu: 'link image table',
            autosave_ask_before_unload: true,
            autosave_interval: '30s',
            autosave_prefix: 'tinymce-autosave-{path}{query}-{id}-',
            autosave_restore_when_empty: false,
            autosave_retention: '2m',
            wordcount: true,
            branding: false,
            promotion: false,
            statusbar: true,
            resize: true,
            autoresize_bottom_margin: 50,
            min_height: 400,
            max_height: 800,
            convert_urls: false,
            relative_urls: false,
            remove_script_host: false,
            extended_valid_elements: 'script[src|async|defer|type|charset]',
            custom_elements: '~svg,~path,~use,~defs,~symbol,~g,~line,~circle,~rect,~polygon,~polyline,~ellipse',
            valid_children: '+body[style],+body[link]',
            valid_classes: {
                '*': 'table-bordered,table-striped,table-hover,img-fluid,float-left,float-right,text-center,text-left,text-right,lead,blockquote,code-block'
            },
            style_formats: [
                { title: 'Headings', items: [
                    { title: 'Heading 1', format: 'h1' },
                    { title: 'Heading 2', format: 'h2' },
                    { title: 'Heading 3', format: 'h3' },
                    { title: 'Heading 4', format: 'h4' },
                    { title: 'Heading 5', format: 'h5' },
                    { title: 'Heading 6', format: 'h6' }
                ]},
                { title: 'Inline', items: [
                    { title: 'Bold', format: 'bold' },
                    { title: 'Italic', format: 'italic' },
                    { title: 'Underline', format: 'underline' },
                    { title: 'Strikethrough', format: 'strikethrough' },
                    { title: 'Superscript', format: 'superscript' },
                    { title: 'Subscript', format: 'subscript' },
                    { title: 'Code', format: 'code' }
                ]},
                { title: 'Blocks', items: [
                    { title: 'Paragraph', format: 'p' },
                    { title: 'Blockquote', format: 'blockquote' },
                    { title: 'Div', format: 'div' },
                    { title: 'Pre', format: 'pre' }
                ]},
                { title: 'Alignment', items: [
                    { title: 'Left', format: 'alignleft' },
                    { title: 'Center', format: 'aligncenter' },
                    { title: 'Right', format: 'alignright' },
                    { title: 'Justify', format: 'alignjustify' }
                ]}
            ],
            formats: {
                alignleft: { selector: 'p,h1,h2,h3,h4,h5,h6,td,th,div,ul,ol,li,table', classes: 'text-left' },
                aligncenter: { selector: 'p,h1,h2,h3,h4,h5,h6,td,th,div,ul,ol,li,table', classes: 'text-center' },
                alignright: { selector: 'p,h1,h2,h3,h4,h5,h6,td,th,div,ul,ol,li,table', classes: 'text-right' },
                alignjustify: { selector: 'p,h1,h2,h3,h4,h5,h6,td,th,div,ul,ol,li,table', classes: 'text-justify' }
            },
            setup: function(editor) {
                editor.on('init', function() {
                    console.log('TinyMCE editor initialized');
                });
                
                editor.on('change', function() {
                    editor.save(); // Save content to textarea
                });
                
                editor.on('submit', function() {
                    editor.save();
                });
            }
        });
    }
});