document.addEventListener('DOMContentLoaded', () => {

    // Global State
    let activeTable = null;

    // DOM Elements
    const loadTableBtn = document.getElementById('loadTableBtn');
    const monthYearInput = document.getElementById('monthYearInput');
    const activeTableStatus = document.getElementById('activeTableStatus');
    
    const transactionForm = document.getElementById('transactionForm');
    const transIdInput = document.getElementById('transId');
    const transDate = document.getElementById('transDate');
    const transCategory = document.getElementById('transCategory');
    const transDesc = document.getElementById('transDesc');
    const transAmount = document.getElementById('transAmount');
    
    const saveBtn = document.getElementById('saveBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    
    const tableBody = document.getElementById('tableBody');
    const sumIncome = document.getElementById('sumIncome');
    const sumExpense = document.getElementById('sumExpense');
    const sumBalance = document.getElementById('sumBalance');
    const tableSpinner = document.getElementById('tableSpinner');
    const toast = document.getElementById('toast');
    const toastMsg = document.getElementById('toastMsg');

    // Default Date to Today
    transDate.valueAsDate = new Date();

    // -- Event Listeners --

    // Load Database Table
    loadTableBtn.addEventListener('click', async () => {
        const val = monthYearInput.value.trim();
        if(!val || val.length !== 7 || !val.includes('_')) {
            showToast('Please enter valid MM_YYYY format', 'error');
            return;
        }

        tableSpinner.classList.remove('hidden');
        try {
            const res = await fetch('/api/load', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ month_year: val })
            });
            const data = await res.json();
            
            if(res.ok) {
                activeTable = data.table_name;
                activeTableStatus.classList.remove('hidden');
                activeTableStatus.querySelector('span').textContent = `${val} Loaded`;
                showToast(`Table ${val} loaded securely.`, 'success');
                fetchData();
            } else {
                showToast(data.error || 'Failed to load table', 'error');
            }
        } catch (err) {
            showToast('Network error connecting to backend.', 'error');
        } finally {
            tableSpinner.classList.add('hidden');
        }
    });

    // Form Submit (Add / Edit)
    transactionForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if(!activeTable) {
            showToast('Please load a month & year first.', 'error');
            return;
        }

        const id = transIdInput.value;
        const payload = {
            date: transDate.value,
            category: transCategory.value,
            description: transDesc.value,
            amount: transAmount.value
        };

        try {
            let res;
            if(id) {
                // Update
                res = await fetch(`/api/transactions/${activeTable}/${id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            } else {
                // Add
                res = await fetch(`/api/transactions/${activeTable}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            }

            const data = await res.json();
            
            if(res.ok) {
                showToast(data.message, 'success');
                resetForm();
                fetchData();
            } else {
                showToast(data.error || 'Failed to process transaction.', 'error');
            }
        } catch (err) {
            showToast('Network error connecting to backend.', 'error');
        }
    });

    // Cancel Edit
    cancelBtn.addEventListener('click', resetForm);

    // -- Helper Functions --

    async function fetchData() {
        if(!activeTable) return;
        tableSpinner.classList.remove('hidden');
        
        try {
            // Fetch Transactions
            const listRes = await fetch(`/api/transactions/${activeTable}`);
            const listData = await listRes.json();
            
            // Fetch Summary
            const sumRes = await fetch(`/api/transactions/summary/${activeTable}`);
            const sumData = await sumRes.json();

            if(listRes.ok && sumRes.ok) {
                renderTable(listData.transactions);
                renderSummary(sumData);
            }
        } catch (err) {
            showToast('Error fetching data.', 'error');
        } finally {
            tableSpinner.classList.add('hidden');
        }
    }

    function renderTable(transactions) {
        tableBody.innerHTML = '';
        
        if(transactions.length === 0) {
            tableBody.innerHTML = `
                <tr class="empty-state-row">
                    <td colspan="6" class="empty-state">
                        <i class="fa-regular fa-folder-open"></i>
                        <p>No transactions found for this month.</p>
                    </td>
                </tr>`;
            return;
        }

        transactions.forEach(t => {
            const tr = document.createElement('tr');
            
            // Amount Formatting
            const isNegative = t.amount < 0;
            const amtClass = isNegative ? 'amt-negative' : 'amt-positive';
            const amtSymbol = isNegative ? '-' : '+';
            const amtValue = Math.abs(t.amount).toLocaleString('en-IN');
            
            // Date Formatting
            const dateObj = new Date(t.date);
            const formattedDate = dateObj.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year:'numeric' });

            tr.innerHTML = `
                <td>#${t.id}</td>
                <td>${formattedDate}</td>
                <td><span class="category-badge">${t.category}</span></td>
                <td>${t.description}</td>
                <td class="text-right ${amtClass}">${amtSymbol}₹${amtValue}</td>
                <td>
                    <div class="action-btns">
                        <button class="btn-icon btn-edit" onclick="editTransaction(${t.id}, '${t.date}', '${t.category}', '${t.description.replace(/'/g, "\\'")}', ${t.amount})" title="Edit">
                            <i class="fa-solid fa-pen"></i>
                        </button>
                        <button class="btn-icon btn-delete" onclick="deleteTransaction(${t.id})" title="Delete">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            tableBody.appendChild(tr);
        });
    }

    function renderSummary(data) {
        sumIncome.textContent = `₹${data.income.toLocaleString('en-IN')}`;
        sumExpense.textContent = `₹${data.expense.toLocaleString('en-IN')}`;
        sumBalance.textContent = `₹${data.balance.toLocaleString('en-IN')}`;
        
        // Color balance
        if(data.balance < 0) sumBalance.style.color = 'var(--danger)';
        else if(data.balance > 0) sumBalance.style.color = 'var(--success)';
        else sumBalance.style.color = 'var(--text-main)';
    }

    window.editTransaction = (id, date, category, desc, amount) => {
        // Scroll to top
        document.querySelector('.sidebar').scrollTop = 0;
        
        transIdInput.value = id;
        
        // Ensure Date is YYYY-MM-DD
        const d = new Date(date);
        transDate.value = d.toISOString().split('T')[0];
        
        transCategory.value = category;
        transDesc.value = desc;
        transAmount.value = amount;
        
        saveBtn.textContent = "Save Changes";
        cancelBtn.classList.remove('hidden');
    };

    window.deleteTransaction = async (id) => {
        if(!confirm("Are you sure you want to delete this transaction?")) return;
        
        try {
            const res = await fetch(`/api/transactions/${activeTable}/${id}`, {
                method: 'DELETE'
            });
            const data = await res.json();
            
            if(res.ok) {
                showToast('Deleted successfully', 'success');
                fetchData();
            } else {
                showToast(data.error || 'Failed to delete', 'error');
            }
        } catch (err) {
            showToast('Network error', 'error');
        }
    };

    function resetForm() {
        transIdInput.value = '';
        transDate.valueAsDate = new Date();
        transCategory.value = '';
        transDesc.value = '';
        transAmount.value = '';
        
        saveBtn.textContent = "Add Transaction";
        cancelBtn.classList.add('hidden');
    }

    function showToast(msg, type = 'info') {
        toastMsg.textContent = msg;
        
        toast.className = 'toast'; // reset
        if(type === 'error') toast.classList.add('error');
        else if(type === 'success') toast.classList.add('success');
        
        toast.classList.add('show');
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
});
