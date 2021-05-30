let generateUUID = () => {
    let d = new Date().getTime(); //Timestamp#}
    let d2 = (performance && performance.now && (performance.now() * 1000)) || 0; //Time in microseconds since page-load or 0 if unsupported#}
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        let r = Math.random() * 16; //random number between 0 and 16#}
        if (d > 0) { //Use timestamp until depleted#}
            r = (d + r) % 16 | 0;
            d = Math.floor(d / 16);
        } else { //Use microseconds since page-load if supported#}
            r = (d2 + r) % 16 | 0;
            d2 = Math.floor(d2 / 16);
        }
        return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
}
let get_files_by_upload_id = () => {

    const upload_id = document.getElementById("upload_id_input").value
    let request = new XMLHttpRequest();
    request.responseType = 'json';
    request.open("GET", `/find/${upload_id}`);
    request.send();
    request.onload = () => {
        if (request.status !== 200) { // analyze HTTP status of the response
            loader(false)
            swal("Something going wrong!", `No valid Upload ID : ${upload_id}`, "error");
        } else {
            loader(false)
            if (request.response !== "") {
                const data = request.response['data']
                if (data.length > 0) {
                    // var table = $('#upload_id_tbl').DataTable();
                    $('#upload_id_tbl').DataTable({
                        data: data,
                        retrieve: true,
                        columns: [
                            { title: "Object ID" },
                            { title: "File" },
                            { title: "Play" },
                            { title: "Download" },
                        ],
                        columnDefs: [{
                                targets: 2,
                                render: function(data, type) {
                                    if (type === 'display') {
                                        data = '<a href="' + 'render/' + data + '/" target="_blank">Play</a>';
                                    }
                                    return data;
                                }
                            },
                            {
                                targets: 3,
                                render: function(data, type) {
                                    if (type === 'display') {
                                        data = '<a href="' + 'render/' + data + '/" target="_blank">Download</a>';
                                    }
                                    return data;
                                }
                            }
                        ],

                    });

                }
                modal.show()
            } else {
                swal("Something going wrong!", `Unable to fetch data for upload id : ${upload_id}`, "error");
            }
        }

    }
    request.onerror = () => {
        loader(false)
        alert("Request failed");
    }
};
let find_by_object_id = (file_id) => {

    let request = new XMLHttpRequest();
    const url = '/file/' + file_id
    request.open("GET", url);
    request.send();

    request.onload = () => {
        if (request.status !== 200) { // analyze HTTP status of the response
            loader(false)
            swal("Something going wrong!", `No valid Object ID : ${file_id}`, "error");
        } else {
            loader(false)
            if (request.response !== "") {
                const data = JSON.parse(request.response)
                document.getElementById("modal_file_title").innerText = "File Details for Object id : " + file_id
                document.getElementById("object_title").innerText = data['title']
                document.getElementById("object_format").innerText = data['format_type']
                document.getElementById("object_file_size").innerText = data['file_size']
                document.getElementById("object_created").innerText = data['created_at'].toString()
                file_details.show()
            } else {
                swal("Something going wrong!", request.response, "error");
            }
        }

    }
}
let find_upload = document.getElementById('find_upload');
let find_object = document.getElementById('find_object');
find_upload.addEventListener('submit', function(e) {
    e.preventDefault();
    loader(true)
    get_files_by_upload_id()
});

find_object.addEventListener('submit', function(e) {
    e.preventDefault();
    loader(true)
    let file = document.getElementById("file_object_id")
    let file_id = file.value
    if (file_id !== "") {
        find_by_object_id(file_id)
        file.value = ""
    }
});

let create_batch = (job_id) => {

        let formData = new FormData();
        let request = new XMLHttpRequest();
        const url = '/create_batch'
        formData.set('uuid', job_id);
        request.open("POST", url);
        request.send(formData);
        request.onload = () => {
            swal("Something going wrong!", `Error : ${request.response}`, "error");
            if (request.status !== 200) { // analyze HTTP status of the response
                swal("Something going wrong!", `Error : ${request.response}`, "error");
            } else {
                loader(false)
                swal("Good job! Please save the upload ID", `Upload ID : ${request.response}`, "success").then(() => {
                    let upload_id_div = document.getElementById("upload_id")
                    upload_id_div.innerHTML = 'Upload ID :' +
                        '<div class="alert-link" style="font-size: large;">' + request.response + '</div>.'
                    upload_id_div.style.display = ""
                    let upload_input = document.getElementById("upload_id_input")
                    upload_input.value = request.response
                    document.getElementById("exampleModalLabel").innerText = "Files for Upload id : " + job_id
                    get_files_by_upload_id()
                });

            }
        }
    }
    // Constants
let UPLOAD_URL = "/upload";
const job_uuid = generateUUID()
    // List of pending files to handle when the Upload button is finally clicked.
let PENDING_FILES = [];
let upload_modal = document.getElementById("modal")
let file_details_modal = document.getElementById("modal_file")
let modal = new bootstrap.Modal(upload_modal)
let file_details = new bootstrap.Modal(file_details_modal)

let loader = (enable) => {
    let loader_div = document.getElementById("loader");
    if (enable === true) {
        loader_div.style.display = "block"
    } else {
        loader_div.style.display = "none"
    }

}
$(document).ready(function() {
    // Set up the drag/drop zone.
    initDropbox();

    // Set up the handler for the file input box.
    $("#file-input").on("change", function() {
        handleFiles(this.files);
    });

    // Handle the submit button.
    $("#upload-button").on("click", function(e) {
        // If the user has JS disabled, none of this code is running but the
        // file multi-upload input box should still work. In this case they'll
        // just POST to the upload endpoint directly. However, with JS we'll do
        // the POST using ajax and then redirect them ourself when done.
        e.preventDefault();
        loader(true)
        doUpload();
    })
});


function doUpload() {
    $("#progress").show();
    let $progressBar = $("#progress-bar");

    // Gray out the form.
    $("#upload :input").attr("disabled", "disabled");

    // Initialize the progress bar.
    $progressBar.css({ "width": "0%" });

    // Collect the form data.
    let fd = collectFormData();

    // Attach the files.
    for (let i = 0, ie = PENDING_FILES.length; i < ie; i++) {
        // Collect the other form data.
        fd.append("file", PENDING_FILES[i]);
    }

    // Inform the back-end that we're doing this over ajax.
    fd.append("uuid", job_uuid);
    $.ajax({
        xhr: function() {
            let xhrobj = $.ajaxSettings.xhr();
            if (xhrobj.upload) {
                xhrobj.upload.addEventListener("progress", function(event) {
                    let percent = 0;
                    let position = event.loaded || event.position;
                    let total = event.total;
                    if (event.lengthComputable) {
                        percent = Math.ceil(position / total * 100);
                    }

                    // Set the progress bar.
                    $progressBar.css({ "width": percent + "%" });
                    $progressBar.text(percent + "%");
                }, false)
            }
            return xhrobj;
        },
        url: UPLOAD_URL,
        method: "POST",
        contentType: false,
        processData: false,
        cache: false,
        data: fd,
        success: function(data) {
            $progressBar.css({ "width": "100%" });
            data = JSON.parse(data);
            // How'd it go?
            if (data === "OK") {
                create_batch(job_uuid)
            }
        },
        error: function(data) {
            res = data.responseText.substring(1, data.responseText.length - 1);
            loader(false)
            swal("Something going wrong!", res, "error");
            $("#upload :input").removeAttr("disabled");
        }
    });
}


function collectFormData() {
    // Go through all the form fields and collect their names/values.
    let fd = new FormData();

    $("#upload :input").each(function() {
        let $this = $(this);
        let name = $this.attr("name");
        let type = $this.attr("type") || "";
        let value = $this.val();

        // No name = no care.
        if (name === undefined) {
            return;
        }

        // Skip the file upload box for now.
        if (type === "file") {
            return;
        }


        fd.append(name, value);
    });

    return fd;
}


function handleFiles(files) {
    // Add them to the pending files list.
    for (let i = 0, ie = files.length; i < ie; i++) {
        PENDING_FILES.push(files[i]);
    }
}


function initDropbox() {
    let dropbox = $("#dropbox");

    // On drag enter...
    dropbox.on("dragenter", function(e) {
        e.stopPropagation();
        e.preventDefault();
        $(this).addClass("active");
    });

    // On drag over...
    dropbox.on("dragover", function(e) {
        e.stopPropagation();
        e.preventDefault();
    });

    // On drop...
    dropbox.on("drop", function(e) {
        e.preventDefault();
        $(this).removeClass("active");

        // Get the files.
        let files = e.originalEvent.dataTransfer.files;
        handleFiles(files);

        // Update the display to acknowledge the number of pending files.
        dropbox.text(PENDING_FILES.length + " files ready for upload!");
    });

    // If the files are dropped outside of the drop zone, the browser will
    // redirect to show the files in the window. To avoid that we can prevent
    // the 'drop' event on the document.
    function stopDefault(e) {
        e.stopPropagation();
        e.preventDefault();
    }

    $(document).on("dragenter", stopDefault);
    $(document).on("dragover", stopDefault);
    $(document).on("drop", stopDefault);


}