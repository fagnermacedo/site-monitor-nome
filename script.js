fetch("resultados.json")
  .then(res => res.json())
  .then(data => {
    const tbody = document.querySelector("#tabela tbody");
    data.forEach(reg => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${new Date(reg.data).toLocaleString()}</td>
        <td><a href="${reg.url}" target="_blank">🔗 Link</a></td>
        <td>${reg.trecho}</td>
      `;
      tbody.appendChild(tr);
    });
  });