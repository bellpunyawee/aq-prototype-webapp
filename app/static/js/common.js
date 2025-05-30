// --- Common Utility Functions ---

// From header_template.js: Alert functions
function alertCreation(alert_point, bootstrap_color, message, fadable = false) {
  // Spinner
  var spinner = '<div id="alert_spinner" class="spinner-border spinner-border-sm text-light me-2" role="status"></div>';
  var append_text =
    '<div class="alert alert-' +
    bootstrap_color +
    ' alert-dismissible fade show" role="alert">' + spinner;
  append_text += "<strong>" + message + "</strong>";
  append_text +=
    '<button closeFor="' +
    alert_point +
    '" type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>';
  $(alert_point).html(append_text);
  if (fadable) {
    alertFade(alert_point);
  }
}

function alertCreationTemp(alert_point, bootstrap_color, message, fadable = false) {
  var spinner = '<div id="alert_spinner" class="spinner-border spinner-border-sm text-light me-2" role="status"></div>';
  var append_text =
    '<div class="alert alert-' +
    bootstrap_color +
    ' alert-dismissible fade show" role="alert">' + spinner;
  append_text += "<strong>" + message + "</strong>";
  append_text +=
    '<button closeFor="' +
    alert_point +
    '" type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>';
  $(alert_point).html(append_text);
  if (fadable) {
    alertFadeTemp(alert_point);
  }
}

function alertFade(alert_point) {
  setTimeout(function () {
    $('#alert_spinner').remove();
    $('button[closeFor="' + alert_point + '"]').click();
  }, 5000); // Adjusted fade time to 5s for user to see
}

function alertFadeTemp(alert_point) {
  setTimeout(function () {
    $('#alert_spinner').remove();
    $('button[closeFor="' + alert_point + '"]').click();
    if (typeof loading === 'function') loading(true); // Assuming loading function exists
  }, 5000); // Adjusted fade time
}

// From header_template.js: Loading modal
function loading(state = false) {
  if ($('#loading').length) { // Check if modal exists
    if (state) {
      $('#loading').modal('show');
    } else {
      $('#loading').modal('hide');
    }
  }
}

// From header_template.js: File upload utility
function upload(file_input_id, endpoint) {
  var file_upload = new FileReader();
  file_upload.onload = function (e) {
    var file_base64 = e.target.result;
    $.ajax({
      url: endpoint,
      type: "POST",
      data: JSON.stringify({
        file_content_string: file_base64,
      }),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function (response) {
        if (response.result == "success") {
          if (typeof alertCreation === 'function') alertCreation("#main_alert_point", "success", response.message, true);
        } else {
          if (typeof alertCreation === 'function') alertCreation("#main_alert_point", "danger", response.message);
        }
      },
      error: function() {
        if (typeof alertCreation === 'function') alertCreation("#main_alert_point", "danger", "File upload failed.");
      }
    });
  };
  if (document.getElementById(file_input_id) && document.getElementById(file_input_id).files.length > 0) {
    file_upload.readAsDataURL(document.getElementById(file_input_id).files[0]);
  } else {
    if (typeof alertCreation === 'function') alertCreation("#main_alert_point", "warning", "Please select a file to upload.", true);
  }
}

// From header_template.js: File download utilities
function download(endpoint) {
  $.ajax({
    type: "POST",
    url: endpoint,
    dataType: "json",
    success: function (response) {
      if (response.result == "success") {
        var blob = convertToBlob(
          response.json_string,
          "application/octet-stream"
        );
        makeDownload(blob, response.filename);
      } else {
        if (typeof alertCreation === 'function') alertCreation(
          "#nonsession_alert_point", // Or a more generic alert point
          "danger",
          "Unable to download requested file"
        );
      }
    },
    error: function() {
        if (typeof alertCreation === 'function') alertCreation(
          "#nonsession_alert_point", // Or a more generic alert point
          "danger",
          "Error requesting file download."
        );
    }
  });
}

function convertToBlob(json_string, mimeType) {
  var byteCharacters = atob(json_string);
  var byteNumbers = new Array(byteCharacters.length);
  for (var i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i);
  }
  var byteArray = new Uint8Array(byteNumbers);
  var blob = new Blob([byteArray], { type: mimeType });
  return blob;
}

function makeDownload(blob, filename) {
  var url = URL.createObjectURL(blob);
  var a = document.createElement("a");
  a.style.display = "none";
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

// From header_template.js: Date formatting utility
function convertEpochToFormat(epochTime) {
  var date = new Date(epochTime * 1000);
  var year = date.getFullYear();
  var month = String(date.getMonth() + 1).padStart(2, "0");
  var day = String(date.getDate()).padStart(2, "0");
  var hour = String(date.getHours()).padStart(2, "0");
  var minute = String(date.getMinutes()).padStart(2, "0");
  var second = String(date.getSeconds()).padStart(2, "0");
  return day + "-" + month + "-" + year + " " + hour + ":" + minute + ":" + second;
}

// From dashboard.js: Charting utilities
function presentChart(
  object_id,
  chart_status_id,
  dataset,
  title,
  label_name_array = [],
  bar_top_function = null,
  legend_name = "",
  map_data = []
) {
  if (!$('#' + object_id).length) return; // Don't proceed if chart canvas doesn't exist

  var labels = [];
  var data_array = [];
  var is_chart_existed = Chart.getChart(object_id); // Pass ID directly to getChart

  if (is_chart_existed) {
    is_chart_existed.destroy();
  }

  if (dataset && dataset.hasOwnProperty("Data Point") && dataset["Data Point"].length > 0) {
    for (let i = 0; i < dataset["Data Point"].length; i++) {
      if (label_name_array.length > 0 && label_name_array.length == dataset["Data Point"].length) {
        labels.push(label_name_array[i]);
      } else if (dataset.Timestamp && dataset.Timestamp[i]) {
        labels.push(convertEpochToFormat(dataset.Timestamp[i]));
      } else {
        labels.push('Label ' + (i+1)); // Fallback label
      }
      data_array.push(dataset["Data Point"][i]);
    }

    var configure_legend_name = legend_name || "Value";
    var legend_enable = !!legend_name;
    var padding_top_val = (bar_top_function == null && map_data.length == 0) ? 0 : 40;

    const datasets_arr = [ // Renamed to avoid conflict
      {
        label: configure_legend_name,
        data: data_array,
        borderColor: "#e9953b", // NUS Orange
        backgroundColor: "rgba(239, 124, 0, 0.75)", // NUS Orange with transparency
        borderWidth: 1,
      },
    ];

    const chart_config = {
      type: "bar",
      data: {
        labels: labels,
        datasets: datasets_arr,
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: { display: true, text: title, color: "Black", font: { weight: "bold", size: 20 } },
          datalabels: {
            anchor: "end", align: "end", color: "black", font: { size: 15 }, rotation: -45,
            formatter: function (value, context) {
              var data_val = ""; // Renamed to avoid conflict
              if (bar_top_function != null) {
                data_val = bar_top_function(value);
              } else if (map_data.length > 0 && context.dataIndex < map_data.length) {
                data_val = map_data[context.dataIndex];
              }
              return data_val;
            },
          },
          legend: { display: legend_enable },
        },
        scales: { y: { beginAtZero: true, max: 100, title: { display: true, text: "Percentage score", color: "Black", font: { size: 15, weight: "bold" } } } },
        layout: { padding: { top: padding_top_val } },
      },
    };
    if ($('#' + chart_status_id).length) $('#' + chart_status_id).html("");
    if (typeof ChartDataLabels !== 'undefined') Chart.register(ChartDataLabels); else console.warn("ChartDataLabels not defined.");
    new Chart(document.getElementById(object_id), chart_config);
  } else {
    if ($('#' + chart_status_id).length) $('#' + chart_status_id).html(
      "<h4 class=\"text-center\">We couldn't find any assessment data for you at the moment. If you haven't taken the quiz yet, please start it to proceed.</h4>"
    );
  }
}

function interpretPerformance(ability_value) {
  var ceiling_value = parseInt(Math.ceil(ability_value));
  var data_str = "Unknown"; // Renamed
  if (ceiling_value <= -2) { data_str = "Beginner"; }
  else if (ceiling_value == -1) { data_str = "Novice"; }
  else if (ceiling_value == 0) { data_str = "Competent"; }
  else if (ceiling_value == 1) { data_str = "Skilled"; }
  else if (ceiling_value == 2) { data_str = "Proficient"; }
  else { data_str = "Expert"; }
  return data_str;
}

// From dashboard.js: Get user profile photo (if used in header)
function getProfilePhoto() {
  if (!$('#profile_img').length) return; // Only run if element exists
  $.ajax({
    type: "POST",
    url: "/req_get_profile_picture",
    success: function (response) {
      if (response.result == "success") {
        if (response.photo_string != "") {
          $("#profile_img").attr("src", response.photo_string);
          $("#profile_img").attr("alt", "Embedded Image");
        } else {
          $("#profile_img").attr("src", "/static/images/profile_default.png");
        }
      } else {
        // console.warn("Failed to get profile photo: " + response.status);
        $("#profile_img").attr("src", "/static/images/profile_default.png"); // Fallback
      }
    },
    error: function() {
      // console.error("Error fetching profile photo.");
      $("#profile_img").attr("src", "/static/images/profile_default.png"); // Fallback
    }
  });
}

// Simplified global user info fetcher - updates only global elements like header username/pic
function fetchAndDisplayGlobalUserInfo() {
    $.ajax({
        type: "POST",
        url: "/req_userinfo", // Endpoint to get user information
        success: function(response) {
            if (response.result === "success") {
                if ($("#username_text").length) { // Element in header_template.html
                    $("#username_text").text(response.full_name || 'User');
                }
                if ($("#profile_img").length) { // Element in header_template.html (potentially)
                    if (response.photo_string) {
                        $("#profile_img").attr("src", response.photo_string);
                    } else {
                        $("#profile_img").attr("src", "/static/images/profile_default.png");
                    }
                }
                // Potentially store other frequently accessed global info if needed
                // For example, if user role determines UI elements in header.
            } else {
                // console.warn("Could not fetch global user info: " + response.status);
                 if ($("#username_text").length) $("#username_text").text('Guest');
                 if ($("#profile_img").length) $("#profile_img").attr("src", "/static/images/profile_default.png");
            }
        },
        error: function() {
            // console.error("Error fetching global user info.");
            if ($("#username_text").length) $("#username_text").text('Guest');
            if ($("#profile_img").length) $("#profile_img").attr("src", "/static/images/profile_default.png");
        }
    });
}

// Call global info fetch on document ready for common.js
$(document).ready(function() {
    fetchAndDisplayGlobalUserInfo();
});
