set -ex

CAPACITY=`os-capacity resources group -f json`
CURRENT_DATE=`date`

cat >_footer.html <<EOF
<h2 align="center">Capacity</h2>

<p align="center">Note: this is stale data from $CURRENT_DATE</p>

<div align="center" id="capacity_text">
  <table id="capacity_table">
  <tr>
    <th>Flavors</th>
    <th>Free</th>
    <th>Used</th>
    <th>Total</th>
  <tr>
  <table>
</div>

<script type="application/json" id="capacity_data">
$CAPACITY
</script>

<script type="text/javascript">
  \$( document ).ready(function() {
    var raw = \$("#capacity_data").text();
    var table = \$('#capacity_table');
    var data = JSON.parse(raw);
    \$(data).each(function(index, item) {
      var row = \$('<tr/>');
      row.append(\$('<td>').text(item['Flavors']));
      row.append(\$('<td>').text(item['Free']));
      row.append(\$('<td>').text(item['Used']));
      row.append(\$('<td>').text(item['Total']));
      table.append(row);
    });
});
</script>
EOF

cat _footer.html
