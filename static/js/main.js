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
function fd(num) {
  return (Math.round(num * 100) / 100).toFixed(2);
}
function renderClientLevelTd(group, rows) {
  var open_amount_list = rows.data().pluck("unappliedprog_amt").toArray();
  var open_amount_sum = [...new Set(open_amount_list)].reduce((a, b) => {
    return a + b * 1.0;
  }, 0);

  var allocated_amount_sum = rows
    .data()
    .pluck("allocated_amount")
    .reduce((a, b) => {
      return a + b * 1.0;
    }, 0);

  var unallocated_amount_sum = open_amount_sum - allocated_amount_sum;
  return `
    <td colspan="3">${group} (${rows.count()})</td>
    <td>${fd(allocated_amount_sum)}</td>
    <td>${fd(unallocated_amount_sum)}</td>
    `;
}

function renderInvoiceLevelTd(group, rows) {
  var audit_partner = rows.data().pluck("audit_partner")[0];
  var open_amount_list = rows.data().pluck("unappliedprog_amt").toArray();
  var open_amount_sum = [...new Set(open_amount_list)].reduce((a, b) => {
    return a + b * 1.0;
  }, 0);

  var allocated_amount_sum = rows
    .data()
    .pluck("allocated_amount")
    .reduce((a, b) => {
      return a + b * 1.0;
    }, 0);

  var unallocated_amount_sum = open_amount_sum - allocated_amount_sum;

  return `
    <td colspan="1">${group} (${rows.count()})</td>
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
      decimal: ",",
      thousands: ".",
      search: "Search by Client ID, Name and Audit Partner",
      searchPlaceholder: "Search",
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
        data: "project_name",
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

        createdCell: function (td, cellData, rowData, row, col) {
          if (cellData < 1) {
            $(td).css("color", "red");
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
    },

    order: [
      [0, "asc"],
      [1, "asc"],
    ],
    columnDefs: [
      {
        targets: [0, 1, 2],
        visible: false,
      },
      { width: "50%", targets: 3 },
    ],
    stripeClasses: [],
    paging: true,
    serverSide: true,
    processing: true,
    pageLength: 50,
    ordering: false,
    searching: true,
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
          all = top + parent + group;
        }

        var collapsed = !!collapsedGroups[all];

        rows.nodes().each(function (r) {
          r.style.display = collapsed ? "none" : "";
        });

        return (
          $("<tr/>")
            .append(td_row)
            // .append("<td >" + group + " (" + rows.count() + ")</td>")
            // .append("<td >" + group + " (" + rows.count() + ")</td>")
            // .append("<td >" + group + " (" + rows.count() + ")</td>")
            // .append("<td >" + group + " (" + rows.count() + ")</td>")
            .attr("data-name", all)
            .toggleClass("collapsed", collapsed)
        );
      },
    },
    buttons: [
      {
        extend: "selected", // Bind to Selected row
        text: "Edit",
        name: "edit", // do not change name
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
              console.log(e);
              Swal.fire({
                title: "Error!",
                text: "Error",
                icon: "error",
              });
            },
          });
        },
      },
      // {
      //   extend: "excel",
      //   text: '<i class="fas fa-file-excel fa-2x"></i> Excel',
      //   className: "btn-outline-secondary text-success",
      //   init: function (api, node, config) {
      //     $(node).removeClass("btn-secondary");
      //   },
      //   action: function (e, dt, node, config) {
      //     var that = this;
      //     // isLoading("Descargando excel"); // function to show a loading spin

      //     setTimeout(function () {
      //       // it will download and hide the loading spin when excel is ready
      //       exportExtension = "Excel";
      //       $.fn.DataTable.ext.buttons.excelHtml5.action.call(
      //         that,
      //         e,
      //         dt,
      //         node,
      //         config
      //       );
      //       // swal.close(); // close spin
      //     }, 1000);
      //   },
      // },
    ],
    onEditRow: function (datatable, rowdata, success, error) {
      console.log(rowdata);
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
          console.log(error);
        },
      });
    },
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
});
