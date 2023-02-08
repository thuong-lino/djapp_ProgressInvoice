function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
function numberWithCommas(x) {
  return x;
}
function fd(num) {
  return (Math.round(num * 100) / 100)
    .toFixed(2)
    .toString()
    .replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}
function renderClientLevelTd(group, rows) {
  var open_amount_sum = 0;
  rows
    .data()
    .toArray()
    .forEach((element) => {
      if (element["project_ident"] === null) {
        open_amount_sum += parseFloat(element["unappliedprog_amt"]);
      }
    });

  var allocated_amount_sum = rows
    .data()
    .pluck("allocated_amount")
    .reduce((a, b) => {
      return a + b * 1.0;
    }, 0);

  var unallocated_amount_sum = open_amount_sum - allocated_amount_sum;

  return `
    <td colspan="3">${group}</td>
    <td>${fd(allocated_amount_sum)}</td>
    <td>${fd(unallocated_amount_sum)}</td>
    `;
}

function renderInvoiceLevelTd(group, rows) {
  var audit_partner = rows.data().pluck("audit_partner")[0];
  var open_amount_sum = 0;
  rows
    .data()
    .toArray()
    .forEach((element) => {
      if (element["project_ident"] === null) {
        open_amount_sum += parseFloat(element["unappliedprog_amt"]);
      }
    });

  var allocated_amount_sum = rows
    .data()
    .pluck("allocated_amount")
    .reduce((a, b) => {
      return a + b * 1.0;
    }, 0);

  var unallocated_amount_sum = open_amount_sum - allocated_amount_sum;

  return `
    <td colspan="1">${group}</td>
    <td>${audit_partner}</td>
    <td>${fd(open_amount_sum)}</td>
    <td>${fd(allocated_amount_sum)}</td>
    <td>${fd(unallocated_amount_sum)}</td>
    `;
}
$(document).ready(function () {
  var collapsedGroups = {};
  var top = "";
  var parent = "";

  var table = $("#table_allocation").DataTable({
    language: {
      thousands: ",",
      search: "",
      searchPlaceholder: "Search by Client ID, Name",
    },
    ajax: {
      url: "api/data/",
      dataSrc: "data",
    },

    columns: [
      { data: "id", title: "Allocation ID", type: "readonly" },
      { data: "display_client_name", title: "Client Name", type: "readonly" },
      {
        data: "display_invoice_name",
        title: "Invoice",
        type: "readonly",
      },
      {
        data: "display_project_name",
        title: "Project Name",
        class: "order_id",
        type: "readonly",
      },
      {
        data: null,
        defaultContent: "",
        title: "Audit Partner",
        type: "readonly",
      },
      {
        data: null,
        defaultContent: "",
        title: "Unapplied Progress Amount",
        type: "readonly",
      },

      {
        data: "allocated_amount",
        title: "Allocated Amount",
        type: "number",
        step: 0.01,
        render: $.fn.dataTable.render.number(",", ".", 2),

        createdCell: function (td, cellData, rowData, row, col) {
          $(td).css("text-decoration", "underline");
          $(td).css("text-decoration-style", "double");
          if (cellData == 0) {
            $(td).css("color", "red");
          }
          if (rowData["is_auto_applied_amount"] === true) {
            $(td).append(" (auto allocated)");
          }
        },
      },
      {
        // data: "remaining_amount",
        data: null,
        defaultContent: "",
        title: "Un-Allocated Amount",
        type: "readonly",
      },
    ],
    createdRow: function (row, data, dataIndex) {
      if (data["is_alloc_active"] == false) {
        $(row).addClass("row-disabled");
      }
      if (data["project_status"] == "Complete") {
        $(row).addClass("row-completed-project");
      }
    },

    columnDefs: [
      {
        targets: [0, 1, 2],
        visible: false,
      },
      { width: "50%", targets: 3 },
      { targets: 7, type: "num-fmt" },
    ],
    stripeClasses: [],
    paging: false,
    pageLength: 50,
    serverSide: true,
    processing: true,
    searching: true,
    search: {
      return: true,
    },
    select: true,
    responsive: true,
    altEditor: true, // Enable altEditor
    dom: "Bfrtip", // Needs button container
    // fixedColumns: {
    //   left: 1,
    // },
    rowGroup: {
      dataSrc: ["display_client_name", "display_invoice_name"],
      startRender: function (rows, group, level) {
        var all;
        var td_row;
        //   console.log(group + ", level: " + level);
        if (level === 0) {
          top = group;
          all = group;
          td_row = renderClientLevelTd(group, rows);
        } else if (level === 1) {
          parent = top + group;
          all = parent;
          // td_row = "<td colspan='5' >" + group + " (" + rows.count() + ")</td>";
          td_row = renderInvoiceLevelTd(group, rows);
          // if parent collapsed, nothing to do
          if (!!collapsedGroups[top]) {
            return;
          }
        } else {
          // if parent collapsed, nothing to do
          if (!!collapsedGroups[parent]) {
            return;
          }
          td_row = renderInvoiceLevelTd(group, rows);
          all = top + parent + group;
        }

        var collapsed = !!collapsedGroups[all];

        rows.nodes().each(function (r) {
          r.style.display = collapsed ? "none" : "";
        });

        return $("<tr/>")
          .append(td_row)
          .attr("data-name", all)
          .toggleClass("collapsed", collapsed);
      },
    },
    buttons: [
      {
        extend: "selected", // Bind to Selected row
        text: "Edit",
        name: "edit", // do not change name
        className: "button-edit",
      },
      {
        text: "Refresh All",
        action: function (e, dt, node, config) {
          Swal.fire({
            title: "Refreshing Data...",
            text: "It might took a couple minutes! Please do not close this tab",
            icon: "success",
            showConfirmButton: false,
            allowOutsideClick: false,
            allowEscapeKey: false,
          });

          $.ajax({
            url: "api/refresh_db/",
            type: "post",
            headers: {
              "X-CSRFToken": getCookie("csrftoken"),
            },
            success: function () {
              console.log("reload success");
              dt.ajax.reload();
              Swal.close();
            },
            error: function (e) {
              console.log("reload failed");

              Swal.fire({
                title: "Error!",
                text: "Error",
                icon: "error",
              });
            },
          });
        },
      },
      "spacer",
      {
        text: "Hide 'Completed' Projects",
        action: function (e, dt, node, config) {
          if (node.text() == "Display 'Completed' Projects") {
            node.text("Hide 'Completed' Projects");
            dt.rows(".row-completed-project").nodes().to$().css("display", "");
          } else {
            node.text("Display 'Completed' Projects");
            dt.rows(".row-completed-project")
              .nodes()
              .to$()
              .css("display", "none");
          }
        },
      },
    ],
    onEditRow: function (datatable, rowdata, success, error) {
      $.ajax({
        // a tipycal url would be /{id} with type='POST'
        url: "api/data/" + rowdata.id + "/",
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
        },
        type: "PUT",
        data: rowdata,
        success: success,
        error: (error) => {
          console.log(error.responseJSON.error);
          Swal.fire({
            title: "Allocation Error!",
            text: error.responseJSON.error,
            icon: "error",
          });
        },
      });
    },
  });
  // Setup - add a text input to each headers cell
  $("#table_allocation_filter").each(function () {
    var title = $(this).text();
    element = `<label><input type="search" id='audit_partner_search' class="form-control form-control-sm" placeholder="Search Audit Partner" aria-controls="table_allocation"></label>`;
    $(this).prepend(element);
  });
  $("#audit_partner_search").on("keyup change", function (event) {
    var keycode = event.keyCode ? event.keyCode : event.which;

    if (keycode == "13") {
      table.columns(4).search(this.value).draw();
    }

    // if (table.search() !== this.value) {
    //      table.search(this.value).draw();
    // }
  });
  $("#table_allocation").on("dblclick", "tbody tr", function () {
    table.rows(this).select();
    table.button("0").trigger();
    //  table.rows(this).deselect();
  });
  $("#table_allocation tbody").on("click", "tr.dtrg-start", function () {
    var name = $(this).data("name");
    collapsedGroups[name] = !collapsedGroups[name];
    table.draw(false);
  });
  $(".modal").on("shown.bs.modal", function (e) {
    $("#allocated_amount").select();
  });
  $(".modal").on("hidden.bs.modal", function (e) {
    selected_row = table.rows(".selected").deselect();
  });

  $("#table_allocation").on("draw.dt", function () {
    var open_amount_sum = 0;
    rows = table.rows();
    rows
      .data()
      .toArray()
      .forEach((element) => {
        if (element["project_ident"] === null) {
          open_amount_sum += parseFloat(element["unappliedprog_amt"]);
        }
      });

    var allocated_amount_sum = rows
      .data()
      .pluck("allocated_amount")
      .reduce((a, b) => {
        return a + b * 1.0;
      }, 0);

    var unallocated_amount_sum = open_amount_sum - allocated_amount_sum;
    $("#total_unallocated").text(fd(unallocated_amount_sum));
  });
});
