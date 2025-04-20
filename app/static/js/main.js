document.addEventListener('DOMContentLoaded', function() {
    // Check if user is authenticated by looking for logout button
    const isAuthenticated = document.querySelector('a[href*="logout"]') !== null;
    
    if (isAuthenticated) {
        // Load initial data only if user is authenticated
        loadTransactions();
        loadSummary();
    } else {
        // If not authenticated, show empty state
        document.getElementById('transactionsList').innerHTML = '<div class="text-center">Please log in to view transactions</div>';
        document.getElementById('totalIncome').textContent = '$0.00';
        document.getElementById('totalExpenses').textContent = '$0.00';
        document.getElementById('balance').textContent = '$0.00';
    }

    // Add transaction form submission
    document.getElementById('transactionForm')?.addEventListener('submit', function(e) {
        e.preventDefault();
        const amount = parseFloat(document.getElementById('amount').value);
        const category = document.getElementById('category').value;
        const transactionType = document.getElementById('transactionType').value;
        const description = document.getElementById('description').value;

        if (!amount || !category || !transactionType) {
            alert('Please fill in all required fields');
            return;
        }

        fetch('/transactions/add_transaction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                amount: amount,
                category: category,
                transaction_type: transactionType,
                description: description
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            document.getElementById('transactionForm').reset();
            loadTransactions();
            loadSummary();
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error adding transaction: ' + error.message);
        });
    });

    // PDF upload form submission
    document.getElementById('pdfForm')?.addEventListener('submit', function(e) {
        e.preventDefault();
        const fileInput = document.getElementById('pdfFile');
        const file = fileInput.files[0];

        if (!file) {
            alert('Please select a PDF file');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        fetch('/transactions/upload_pdf', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            fileInput.value = '';
            loadTransactions();
            loadSummary();
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
            const transactionsList = document.getElementById('transactionsList');
            transactionsList.innerHTML = '';

            if (data.transactions && data.transactions.length > 0) {
                data.transactions.forEach(transaction => {
                    const transactionElement = document.createElement('div');
                    transactionElement.className = 'transaction-item';
                    
                    const transactionInfo = document.createElement('div');
                    transactionInfo.className = 'transaction-info';
                    
                    const category = document.createElement('div');
                    category.className = 'transaction-category';
                    category.textContent = transaction.category;
                    
                    const description = document.createElement('div');
                    description.className = 'transaction-description';
                    description.textContent = transaction.description || 'No description';
                    
                    const date = document.createElement('div');
                    date.className = 'transaction-date';
                    date.textContent = new Date(transaction.date).toLocaleDateString();
                    
                    transactionInfo.appendChild(category);
                    transactionInfo.appendChild(description);
                    transactionInfo.appendChild(date);
                    
                    const amount = document.createElement('div');
                    amount.className = `transaction-amount ${transaction.transaction_type}`;
                    amount.textContent = `$${Math.abs(transaction.amount).toFixed(2)}`;
                    
                    const deleteButton = document.createElement('button');
                    deleteButton.className = 'btn btn-danger';
                    deleteButton.innerHTML = '<i class="fas fa-trash"></i>';
                    deleteButton.onclick = () => deleteTransaction(transaction.id);
                    
                    transactionElement.appendChild(transactionInfo);
                    transactionElement.appendChild(amount);
                    transactionElement.appendChild(deleteButton);
                    
                    transactionsList.appendChild(transactionElement);
                });
            } else {
                transactionsList.innerHTML = '<div class="text-center">No transactions found</div>';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            const transactionsList = document.getElementById('transactionsList');
            transactionsList.innerHTML = '<div class="text-center">Please log in to view transactions</div>';
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
            document.getElementById('totalIncome').textContent = `$${data.total_income.toFixed(2)}`;
            document.getElementById('totalExpenses').textContent = `$${data.total_expenses.toFixed(2)}`;
            document.getElementById('balance').textContent = `$${(data.total_income - data.total_expenses).toFixed(2)}`;

            // Update category chart
            const categoryCtx = document.getElementById('categoryChart');
            if (categoryCtx) {
                new Chart(categoryCtx.getContext('2d'), {
                    type: 'pie',
                    data: {
                        labels: Object.keys(data.by_category),
                        datasets: [{
                            data: Object.values(data.by_category),
                            backgroundColor: [
                                '#10b981',
                                '#3b82f6',
                                '#f59e0b',
                                '#ef4444',
                                '#8b5cf6',
                                '#ec4899',
                                '#14b8a6'
                            ]
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'right'
                            }
                        }
                    }
                });
            }

            // Update monthly chart
            const monthlyCtx = document.getElementById('monthlyChart');
            if (monthlyCtx) {
                new Chart(monthlyCtx.getContext('2d'), {
                    type: 'line',
                    data: {
                        labels: Object.keys(data.monthly_summary),
                        datasets: [{
                            label: 'Monthly Balance',
                            data: Object.values(data.monthly_summary),
                            borderColor: '#3b82f6',
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('totalIncome').textContent = '$0.00';
            document.getElementById('totalExpenses').textContent = '$0.00';
            document.getElementById('balance').textContent = '$0.00';
        });
}

function deleteTransaction(id) {
    if (!confirm('Are you sure you want to delete this transaction?')) {
        return;
    }

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