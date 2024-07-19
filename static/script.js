function filterTable() {
    var inputCodigo, inputNome, inputSaldo, inputCusto, inputSugestao, inputEstoque, 
        filterCodigo, filterNome, filterSaldo, filterCusto, filterSugestao, filterEstoque,
        table, tr, tdCodigo, tdNome, tdSaldo, tdCusto, tdSugestao, tdEstoque, txtValueCodigo, 
        txtValueNome, txtValueSaldo, txtValueCusto, txtValueSugestao, txtValueEstoque, i;

    // Captura dos valores dos inputs de filtro
    inputCodigo = document.getElementById("filter-codigo").value.toUpperCase();
    inputNome = document.getElementById("filter-nome").value.toUpperCase();
    inputSaldo = document.getElementById("filter-saldo").value.toUpperCase();
    inputCusto = document.getElementById("filter-custo").value.toUpperCase();
    inputSugestao = document.getElementById("filter-sugestao").value.toUpperCase();
    inputEstoque = document.getElementById("filter-estoque").value.toUpperCase();

    // Seleciona a tabela e todas as linhas
    table = document.querySelector("table tbody");
    tr = table.getElementsByTagName("tr");

    // Loop através de todas as linhas da tabela e exibe aquelas que correspondem aos filtros
    for (i = 0; i < tr.length; i++) {
        // Seleciona as células relevantes de cada linha
        tdCodigo = tr[i].getElementsByTagName("td")[0];
        tdNome = tr[i].getElementsByTagName("td")[1];
        tdSaldo = tr[i].getElementsByTagName("td")[2];
        tdCusto = tr[i].getElementsByTagName("td")[3];
        tdSugestao = tr[i].getElementsByTagName("td")[4];
        tdEstoque = tr[i].getElementsByTagName("td")[5];

        // Verifica se a linha corresponde aos filtros e a exibe ou oculta conforme necessário
        if (tdCodigo && tdNome && tdSaldo && tdCusto && tdSugestao && tdEstoque) {
            txtValueCodigo = tdCodigo.textContent || tdCodigo.innerText;
            txtValueNome = tdNome.textContent || tdNome.innerText;
            txtValueSaldo = tdSaldo.textContent || tdSaldo.innerText;
            txtValueCusto = tdCusto.textContent || tdCusto.innerText;
            txtValueSugestao = tdSugestao.textContent || tdSugestao.innerText;
            txtValueEstoque = tdEstoque.textContent || tdEstoque.innerText;

            if (txtValueCodigo.toUpperCase().indexOf(inputCodigo) > -1 &&
                txtValueNome.toUpperCase().indexOf(inputNome) > -1 &&
                txtValueSaldo.toUpperCase().indexOf(inputSaldo) > -1 &&
                txtValueCusto.toUpperCase().indexOf(inputCusto) > -1 &&
                txtValueSugestao.toUpperCase().indexOf(inputSugestao) > -1 &&
                txtValueEstoque.toUpperCase().indexOf(inputEstoque) > -1) {
                tr[i].style.display = ""; // Exibe a linha se corresponder aos filtros
            } else {
                tr[i].style.display = "none"; // Oculta a linha se não corresponder aos filtros
            }
        }
    }

    // Exibe todas as linhas se nenhum filtro estiver aplicado
    if (!(inputCodigo || inputNome || inputSaldo || inputCusto || inputSugestao || inputEstoque)) {
        for (i = 0; i < tr.length; i++) {
            tr[i].style.display = "";
        }
    }
}

function exportDataExcel() {
    
    var table = document.querySelector('table'); //para especificar mude 'table' para table[name=xpto_nake]
    var tbody = document.querySelector('tbody'); //para verificar se existe dados na tabela
    var wb = XLSX.utils.table_to_book(table, {sheet: "Sheet JS"});
    var wbout = XLSX.write(wb, {bookType: 'xlsx', type: 'binary'});
    var nomePagina = document.title;

    if (table.rows.length<1){
        console.error('Não há dados a serem exportados!')
        return 0;        
    }

    function s2ab(s) {
        var buf = new ArrayBuffer(s.length);
        var view = new Uint8Array(buf);
        for (var i = 0; i < s.length; i++) view[i] = s.charCodeAt(i) & 0xFF;
        return buf;
    }

    saveAs(new Blob([s2ab(wbout)], {type: "application/octet-stream"}), nomePagina+'.xlsx');
}



