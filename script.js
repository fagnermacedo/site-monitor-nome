fetch("resultados.json")
  .then(res => res.json())
  .then(data => {
    const tbody = document.querySelector("#tabela tbody");
    data.forEach(reg => {
      // Extrai o nome do arquivo da URL
      const url = reg.url;
      const nomeArquivo = url.substring(url.lastIndexOf('/') + 1) || "(página)";

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${new Date(reg.data).toLocaleString()}</td>
        <td><a href="${url}" target="_blank">🔗 Link</a></td>
        <td>${nomeArquivo}</td>  <!-- Coluna "Nome Arquivo" -->
        <td>${reg.trecho}</td>
      `;
      tbody.appendChild(tr);
    });
  });
