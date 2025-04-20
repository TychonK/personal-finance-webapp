document.addEventListener('DOMContentLoaded', function() {
    // Load initial data
    loadTransactions();
    loadSummary();

    // Handle transaction form submission
    document.getElementById('transactionForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const data = {
            amount: parseFloat(document.getElementById('amount').value),
            category: document.getElementById('category').value,
            transaction_type: document.getElementById('transactionType').value,
            description: document.getElementById('description').value || ''
        };

        fetch('/transactions/add_transaction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Success:', data);
            loadTransactions();
            loadSummary();
            document.getElementById('transactionForm').reset();
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error adding transaction: ' + error.message);
        });
    });

    // Handle PDF upload
    document.getElementById('uploadForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData();
        const fileField = document.getElementById('pdfFile');
        formData.append('file', fileField.files[0]);

        fetch('/transactions/upload_pdf', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            loadTransactions();
            loadSummary();
            document.getElementById('uploadForm').reset();
            alert('PDF processed successfully!');
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error processing PDF: ' + error.message);
        });
    });
});

function loadTransactions() {
    fetch('/transactions/get_summary')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            const tbody = document.getElementById('transactionsList');
            tbody.innerHTML = '';
            
            if (data.transactions && Array.isArray(data.transactions)) {
                data.transactions.forEach(transaction => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${new Date(transaction.date).toLocaleDateString()}</td>
                        <td>${transaction.category}</td>
                        <td>${transaction.description || '-'}</td>
                        <td class="${transaction.transaction_type === 'income' ? 'text-success' : 'text-danger'}">
                            ${transaction.transaction_type === 'income' ? '+' : '-'}$${Math.abs(transaction.amount).toFixed(2)}
                        </td>
                        <td>${transaction.transaction_type}</td>
                        <td>
                            <button class="btn btn-sm btn-danger" onclick="deleteTransaction(${transaction.id})">Delete</button>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
            }
        })
        .catch(error => {
            console.error('Error loading transactions:', error);
        });
}

function loadSummary() {
    fetch('/transactions/get_summary')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            document.getElementById('totalIncome').textContent = `$${(data.total_income || 0).toFixed(2)}`;
            document.getElementById('totalExpenses').textContent = `$${(data.total_expenses || 0).toFixed(2)}`;
            updateCharts(data);
        })
        .catch(error => {
            console.error('Error loading summary:', error);
        });
}

function deleteTransaction(id) {
    if (confirm('Are you sure you want to delete this transaction?')) {
        fetch(`/transactions/delete_transaction/${id}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            loadTransactions();
            loadSummary();
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error deleting transaction: ' + error.message);
        });
    }
}

function updateCharts(data) {
    // Implement charts using a library like Chart.js
    // This is a placeholder for chart implementation
    console.log('Update charts with:', data);
} 