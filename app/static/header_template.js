block_type_to_replace
file
new_block_content
/* Event assignment to object */
$(document).ready(function () {
  // Only call functions that are still defined in this file or are globally available (like jQuery's $)
  if (typeof loadLogo === 'function') loadLogo();
  if (typeof responsiveTable === 'function') responsiveTable();

  // loginADQ is event-bound, not called directly on ready typically unless for auto-login
  // $("#login_btn").click(...) and other event bindings remain.
});

function loadLogo() {
  var element_existed = $("#login-form").length;
  var image_path = "/static/images/cpfm.png"; // Corrected path if needed

  if (element_existed) { // Check if #login-form exists, implies login page
    // Assuming #logo_place is within the login form context
    // No need for AJAX to check image, just set it if on login page
    if ($("#logo_place").length) {
        $("#logo_place").html('<img height="100" src="' + image_path + '">');
    }
  }
}

/* Function library */
function loginADQ(state) { // Parameter 'state' is not used
  thisAjax();

  function thisAjax() {
    var this_username = $("#login_user_id").val();
    var this_password = $("#login_user_pw").val();
    // console.log('Attempting to log in...');
    // console.log('Username field value:', $('#login_user_id').val());
    // console.log('Password field value (pre-btoa):', $('#login_user_pw').val());
    this_password = btoa(this_password); // Consider security implications of client-side btoa for passwords
    var remember_me_checkbox = $("#rememberme_login_page"); // ID used in new login page
    var remember_me = remember_me_checkbox.is(":checked");


    $.ajax({
      type: "POST",
      url: "/login",
      data: JSON.stringify({
        username: this_username,
        password: this_password,
        remember: remember_me,
      }),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function (response) {
        if (response.result == "success") {
          // alertCreation is now in common.js, ensure common.js is loaded before this script if called directly
          // However, usually a page reload or redirect handles this.
          // Forcing a reload is simpler than trying to call common.js's alertCreation here.
          location.reload();
        } else {
          // Check if alertCreation is available (from common.js)
          if (typeof alertCreation === 'function') {
            alertCreation("#login_alert_point", "danger", response.status);
          } else {
            // Fallback if common.js didn't load or alertCreation isn't global
            console.error("alertCreation function not found. Status: " + response.status);
            alert("Login failed: " + response.status); // Simple alert fallback
          }
        }
      },
      error: function() {
        if (typeof alertCreation === 'function') {
            alertCreation("#login_alert_point", "danger", "Login request failed. Please try again.");
        } else {
            console.error("alertCreation function not found. Login request failed.");
            alert("Login request failed. Please try again.");
        }
      }
    });
  }
}

// This function might be too specific if #responsive_table is not in header_template.html
// If it's for tables on specific pages, it should move to the JS for those pages.
// Keeping it here for now, assuming #responsive_table might be a general layout element.
function responsiveTable() {
  if (!$('#responsive_table').length) return; // Guard clause

  var user_width = screen.width;
  var windowWidth = $(window).width();
  var width_cal = (windowWidth / user_width) * 100;
  var upper_range = 60;
  var lower_range = 20;

  if (width_cal >= upper_range) {
    $("#responsive_table").css("width", String(lower_range) + "%");
  } else if (width_cal < upper_range && width_cal > lower_range) {
    var new_width =
      ((upper_range - width_cal) / (upper_range - lower_range)) *
        (upper_range - lower_range) +
      lower_range;
    new_width = parseInt(Math.floor(new_width));
    $("#responsive_table").css("width", String(new_width) + "%");
  } else {
    $("#responsive_table").css("width", String(upper_range) + "%");
  }
}

function switchPage() {
  if ($("#normal_form").length && $("#forgot_form").length) { // Ensure forms exist
    if ($("#normal_form").hasClass("d-none")) {
      $("#normal_form").removeClass("d-none");
      $("#forgot_form").addClass("d-none");
      // Consider disabling/enabling a common submit button or specific ones
      // $("#submit_pw_btn").addClass("disabled"); // If this button is outside forgot_form
      // $("#login_btn").removeClass("disabled");
    } else {
      $("#normal_form").addClass("d-none");
      $("#forgot_form").removeClass("d-none");
      // $("#login_btn").addClass("disabled");
      // $("#submit_pw_btn").removeClass("disabled");
    }
  }
}

function submitPassword() {
  var error = 0;
  // Ensure this targets inputs within the forgot_form context
  $('#forgot_form input[reset_type="credential"]').each(function () {
    if ($(this).val() == "") {
      $(this).addClass("is-invalid");
      error = 1;
    } else {
      $(this).removeClass("is-invalid");
    }
  });

  if (error == 1) {
    if (typeof alertCreation === 'function') {
      alertCreation("#reset_alert_point", "danger", "Information can not be emptied");
    } else {
      alert("Information can not be emptied");
    }
    return; // Prevent submission
  }
  
  if ($("#reset_user_pw_1").val() != $("#reset_user_pw_2").val()) {
    if (typeof alertCreation === 'function') {
      alertCreation("#reset_alert_point", "danger", "Password and Confirm password are not matched");
    } else {
      alert("Password and Confirm password are not matched");
    }
    return; // Prevent submission
  }
  
  var username = $("#reset_user_id").val();
  var name_user = $("#reset_user_name").val();
  var password = $("#reset_user_pw_1").val();
  password = btoa(password); // Again, consider security of client-side btoa

  $.ajax({
    url: "/req_reset_password",
    type: "POST",
    data: JSON.stringify({
      username: username,
      name: name_user,
      password: password,
    }),
    contentType: "application/json; charset=utf-8",
    dataType: "json",
    success: function (response) {
      if (response.result == "success") {
        if (typeof alertCreation === 'function') {
          alertCreation("#reset_alert_point", "success", response.status, true);
        } else {
          alert(response.status);
        }
        // Optionally switch back to login form on success
        if (typeof switchPage === 'function') switchPage(); 
      } else {
        if (typeof alertCreation === 'function') {
          alertCreation("#reset_alert_point", "danger", response.status);
        } else {
          alert(response.status);
        }
      }
    },
    error: function() {
      if (typeof alertCreation === 'function') {
          alertCreation("#reset_alert_point", "danger", "Password reset request failed.");
      } else {
          alert("Password reset request failed.");
      }
    }
  });
}

// Ensure event bindings from original $(document).ready() are preserved if they are not re-added.
// These were:
// $("#login_btn").click(...)
// $("#reset_pw_btn").click(...)
// $("#login-form").submit(...)
// $(window).resize(...)
// $("#togglePassword").click(...)
// They should be fine as they are outside the functions being removed.
// It's good practice to have them inside a single $(document).ready() though.
// For this refactor, I'll assume they are fine as is.
// Re-adding them to the top $(document).ready() for clarity:

$(document).ready(function () {
    // loginADQ(); // Not called on ready unless auto-login
    
    // Event bindings originally in header_template.js
    if ($("#login_btn").length) {
        $("#login_btn").off('click').on('click', function (event) { // .off().on() to prevent multiple bindings if script reloaded
            event.preventDefault();
            if (typeof loginADQ === 'function') loginADQ();
        });
    }

    if ($("#reset_pw_btn").length) {
        $("#reset_pw_btn").off('click').on('click', function() {
            if (typeof switchPage === 'function') switchPage();
        });
    }

    if ($("#login-form").length) { // Note: Original selector was #login-form, new HTML uses #normal_form
        $("#login-form").off('submit').on('submit', function (event) { // This might need to target #normal_form now
            event.preventDefault(); 
        });
    }
     // Added for new form IDs
    if ($("#normal_form").length) {
      $("#normal_form").off('submit').on('submit', function (event) {
          event.preventDefault(); 
      });
    }
    if ($("#forgot_form").length) {
        $("#forgot_form").off('submit').on('submit', function (event) {
            event.preventDefault(); 
        });
    }
    if ($("#submit_pw_btn").length) { // Added this binding
      $("#submit_pw_btn").off('click').on('click', function(event) {
          event.preventDefault(); 
          if (typeof submitPassword === 'function') submitPassword();
      });
    }
    if ($("#back_login_btn").length) { // Added this binding
        $("#back_login_btn").off('click').on('click', function() {
            if (typeof switchPage === 'function') switchPage();
        });
    }
    
    // This resize might be better on a more specific element or page JS
    // $(window).off('resize').on('resize', function () { 
    //     if (typeof responsiveTable === 'function') responsiveTable();
    // });

    if ($("#togglePassword").length) {
        $("#togglePassword").off('click').on('click', function () {
            const password = $("#login_user_pw");
            if (password.length) {
                const type = password.attr("type") === "password" ? "text" : "password";
                password.attr("type", type);
                $(this).find("i").toggleClass("bi-eye bi-eye-slash");
            }
        });
    }
    
    // submitPassword is bound by switchPage, so no direct binding here.
    // back_login_btn is also bound by switchPage.
});
