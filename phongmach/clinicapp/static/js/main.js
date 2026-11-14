function addMedicineRow() {
    const container = document.getElementById('medicine-list');
    const firstRow = container.firstElementChild;
    const newRow = firstRow.cloneNode(true);
    newRow.querySelectorAll('input').forEach(input => input.value = input.type === 'number' ? 1 : '');
    container.appendChild(newRow);
}