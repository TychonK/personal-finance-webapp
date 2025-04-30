document.addEventListener('DOMContentLoaded', function() {
    // Check if user is authenticated by looking for logout button
    const isAuthenticated = document.querySelector('a[href*="logout"]') !== null;
    
    if (isAuthenticated) {
        // Load initial data only if user is authenticated
        loadCategories();
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
        const categoryId = document.getElementById('category').value;
        const transactionType = document.getElementById('transactionType').value;
        const description = document.getElementById('description').value;

        if (!amount || !categoryId || !transactionType) {
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
                category_id: categoryId,
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

    // Add category form submission
    document.getElementById('addCategoryForm')?.addEventListener('submit', function(e) {
        e.preventDefault();
        const name = document.getElementById('newCategoryName').value.trim();
        
        if (!name) {
            alert('Please enter a category name');
            return;
        }

        fetch('/categories', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: name })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            document.getElementById('newCategoryName').value = '';
            loadCategories();
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error adding category: ' + error.message);
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

function loadCategories() {
    fetch('/categories')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(categories => {
            // Update transaction form category select
            const categorySelect = document.getElementById('category');
            categorySelect.innerHTML = '<option value="">Select a category</option>';
            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category.id;
                option.textContent = category.name;
                categorySelect.appendChild(option);
            });

            // Update categories list in modal
            const categoriesList = document.getElementById('categoriesList');
            categoriesList.innerHTML = '';
            categories.forEach(category => {
                const item = document.createElement('div');
                item.className = 'list-group-item d-flex justify-content-between align-items-center';
                
                const nameContainer = document.createElement('div');
                nameContainer.className = 'd-flex align-items-center';
                
                const name = document.createElement('span');
                name.className = 'category-name me-2';
                name.textContent = category.name;
                
                if (category.is_default) {
                    const badge = document.createElement('span');
                    badge.className = 'badge badge-default';
                    badge.textContent = 'Default';
                    nameContainer.appendChild(badge);
                }
                
                nameContainer.insertBefore(name, nameContainer.firstChild);
                
                const deleteButton = document.createElement('button');
                deleteButton.className = 'btn btn-danger btn-sm btn-delete-category';
                deleteButton.innerHTML = '<i class="fas fa-trash"></i>';
                deleteButton.disabled = category.is_default;
                deleteButton.onclick = () => deleteCategory(category.id);
                
                item.appendChild(nameContainer);
                item.appendChild(deleteButton);
                categoriesList.appendChild(item);
            });
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

function deleteCategory(categoryId) {
    if (!confirm('Are you sure you want to delete this category? All transactions in this category will be moved to a default category.')) {
        return;
    }

    fetch(`/categories/${categoryId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        loadCategories();
        loadTransactions();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error deleting category: ' + error.message);
    });
}

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

// Global chart instances
let categoryChart = null;
let monthlyChart = null;

// Helper function to destroy chart if it exists
function destroyChart(chart) {
    if (chart instanceof Chart) {
        chart.destroy();
        return null;
    }
    return null;
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
            console.log('Received summary data:', data);
            
            // Update summary numbers with proper formatting
            const formatCurrency = (amount) => {
                return new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: 'USD',
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }).format(amount);
            };

            console.log('Total Income:', data.total_income);
            console.log('Total Expenses:', data.total_expenses);
            console.log('Balance:', data.balance);

            const totalIncomeElement = document.getElementById('totalIncome');
            const totalExpensesElement = document.getElementById('totalExpenses');
            const balanceElement = document.getElementById('balance');

            console.log('Found elements:', {
                totalIncomeElement: !!totalIncomeElement,
                totalExpensesElement: !!totalExpensesElement,
                balanceElement: !!balanceElement
            });

            const formattedIncome = formatCurrency(data.total_income);
            const formattedExpenses = formatCurrency(data.total_expenses);
            const formattedBalance = formatCurrency(data.balance);

            console.log('Formatted values:', {
                income: formattedIncome,
                expenses: formattedExpenses,
                balance: formattedBalance
            });

            // Force DOM update with a small delay
            setTimeout(() => {
                if (totalIncomeElement) {
                    totalIncomeElement.innerHTML = formattedIncome;
                    // Force a DOM reflow
                    void totalIncomeElement.offsetHeight;
                }
                if (totalExpensesElement) {
                    totalExpensesElement.innerHTML = formattedExpenses;
                    void totalExpensesElement.offsetHeight;
                }
                if (balanceElement) {
                    balanceElement.innerHTML = formattedBalance;
                    void balanceElement.offsetHeight;
                    balanceElement.classList.remove('text-success', 'text-danger');
                    if (data.balance >= 0) {
                        balanceElement.classList.add('text-success');
                    } else {
                        balanceElement.classList.add('text-danger');
                    }
                }
            }, 100);

            // Update category chart
            try {
                const categoryCtx = document.getElementById('categoryChart');
                if (categoryCtx) {
                    // Clean up existing chart
                    categoryChart = destroyChart(categoryChart);

                    // Prepare data for the chart
                    const categories = Object.entries(data.by_category || {})
                        .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1])); // Sort by amount

                    if (categories.length > 0) {
                        const labels = categories.map(([name]) => name);
                        const amounts = categories.map(([_, amount]) => Math.abs(amount));

                        console.log('Category data for chart:', { labels, amounts });

                        // Generate colors for categories
                        const colors = generateCategoryColors(categories.length);

                        categoryChart = new Chart(categoryCtx, {
                            type: 'pie',
                            data: {
                                labels: labels,
                                datasets: [{
                                    data: amounts,
                                    backgroundColor: colors,
                                    borderWidth: 1,
                                    borderColor: '#fff'
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    legend: {
                                        position: 'right',
                                        labels: {
                                            padding: 20,
                                            font: {
                                                size: 12
                                            },
                                            generateLabels: function(chart) {
                                                const data = chart.data;
                                                if (data.labels.length && data.datasets.length) {
                                                    return data.labels.map((label, i) => {
                                                        const value = data.datasets[0].data[i];
                                                        return {
                                                            text: `${label} (${formatCurrency(value)})`,
                                                            fillStyle: data.datasets[0].backgroundColor[i],
                                                            hidden: isNaN(data.datasets[0].data[i]),
                                                            lineCap: 'butt',
                                                            lineDash: [],
                                                            lineDashOffset: 0,
                                                            lineJoin: 'miter',
                                                            lineWidth: 1,
                                                            strokeStyle: data.datasets[0].backgroundColor[i],
                                                            pointStyle: 'circle',
                                                            rotation: 0
                                                        };
                                                    });
                                                }
                                                return [];
                                            }
                                        }
                                    },
                                    tooltip: {
                                        callbacks: {
                                            label: function(context) {
                                                const label = context.label || '';
                                                const value = context.raw || 0;
                                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                                const percentage = ((value / total) * 100).toFixed(1);
                                                return `${label}: ${formatCurrency(value)} (${percentage}%)`;
                                            }
                                        }
                                    }
                                }
                            }
                        });
                    }
                }

                // Update monthly chart
                const monthlyCtx = document.getElementById('monthlyChart');
                if (monthlyCtx) {
                    // Clean up existing chart
                    monthlyChart = destroyChart(monthlyChart);

                    const months = Object.keys(data.monthly_summary || {}).sort();
                    const balances = months.map(month => data.monthly_summary[month]);

                    if (months.length > 0) {
                        console.log('Monthly data for chart:', { months, balances });

                        monthlyChart = new Chart(monthlyCtx, {
                            type: 'line',
                            data: {
                                labels: months,
                                datasets: [{
                                    label: 'Monthly Balance',
                                    data: balances,
                                    borderColor: '#3b82f6',
                                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                                    fill: true,
                                    tension: 0.4
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    legend: {
                                        display: false
                                    },
                                    tooltip: {
                                        callbacks: {
                                            label: function(context) {
                                                return `Balance: ${formatCurrency(context.raw)}`;
                                            }
                                        }
                                    }
                                },
                                scales: {
                                    y: {
                                        beginAtZero: false,
                                        grid: {
                                            color: 'rgba(0, 0, 0, 0.1)'
                                        },
                                        ticks: {
                                            callback: function(value) {
                                                return formatCurrency(value);
                                            }
                                        }
                                    },
                                    x: {
                                        grid: {
                                            display: false
                                        }
                                    }
                                }
                            }
                        });
                    }
                }
            } catch (error) {
                console.error('Error creating charts:', error);
            }
        })
        .catch(error => {
            console.error('Error loading summary:', error);
            document.getElementById('totalIncome').textContent = '$0.00';
            document.getElementById('totalExpenses').textContent = '$0.00';
            document.getElementById('balance').textContent = '$0.00';
        });
}

// Helper function to generate colors for categories
function generateCategoryColors(count) {
    const colors = [
        '#10b981', // Green
        '#3b82f6', // Blue
        '#f59e0b', // Yellow
        '#ef4444', // Red
        '#8b5cf6', // Purple
        '#ec4899', // Pink
        '#14b8a6', // Teal
        '#f97316', // Orange
        '#06b6d4', // Cyan
        '#84cc16'  // Lime
    ];

    // If we need more colors than we have, generate random ones
    if (count > colors.length) {
        const additionalColors = Array(count - colors.length).fill().map(() => {
            const hue = Math.random() * 360;
            return `hsl(${hue}, 70%, 60%)`;
        });
        return [...colors, ...additionalColors];
    }

    return colors.slice(0, count);
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