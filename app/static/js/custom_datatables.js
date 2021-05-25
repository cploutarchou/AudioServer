window.addEventListener('DOMContentLoaded', event => {
    const top_10_table = document.getElementById('top_10');
    let table = new simpleDatatables.DataTable(top_10_table, {
        searchable: false,
        fixedHeight: true,
        ordering: true,
        select: false,
        paging: false,
    });
});
