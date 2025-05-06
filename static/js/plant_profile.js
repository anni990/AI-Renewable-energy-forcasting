document.addEventListener('DOMContentLoaded', function() {
    // Handle tab switching
    const tabs = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.add('hidden'));
            
            // Add active class to clicked tab
            tab.classList.add('active');
            
            // Show corresponding content
            const contentId = tab.id.replace('tab-', 'content-');
            document.getElementById(contentId).classList.remove('hidden');
        });
    });
    
    // Add Plant Modal Functionality
    const addPlantBtn = document.getElementById('add-plant-btn');
    const addPlantModal = document.getElementById('add-plant-modal');
    const closeAddModal = document.getElementById('close-add-modal');
    const cancelAdd = document.getElementById('cancel-add');
    
    if (addPlantBtn && addPlantModal) {
        addPlantBtn.addEventListener('click', () => {
            addPlantModal.classList.remove('hidden');
        });
        
        if (closeAddModal) {
            closeAddModal.addEventListener('click', () => {
                addPlantModal.classList.add('hidden');
            });
        }
        
        if (cancelAdd) {
            cancelAdd.addEventListener('click', () => {
                addPlantModal.classList.add('hidden');
            });
        }
    }
    
    // Edit Plant Modal Functionality
    const editBtns = document.querySelectorAll('.edit-plant-btn');
    const editPlantModal = document.getElementById('edit-plant-modal');
    const closeEditModal = document.getElementById('close-edit-modal');
    const cancelEdit = document.getElementById('cancel-edit');
    
    if (editBtns.length && editPlantModal) {
        editBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const plantId = btn.getAttribute('data-plant-id');
                
                // Show loading state for edit modal
                const editForm = document.getElementById('edit-plant-form');
                if (editForm) {
                    editForm.innerHTML = `
                        <div class="flex items-center justify-center p-5">
                            <svg class="animate-spin -ml-1 mr-3 h-8 w-8 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            <span class="text-lg font-medium text-primary-800">Loading plant data...</span>
                        </div>
                    `;
                }
                
                // Show the modal
                editPlantModal.classList.remove('hidden');
                
                // Fetch plant data
                fetch(`/api/plant/${plantId}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            const plant = data.plant;
                            // Restore form and populate with data
                            editForm.innerHTML = `
                                <input type="hidden" id="edit_plant_id" name="plant_id" value="${plant.id}">
                                <input type="hidden" name="action" value="edit">
                                
                                <div>
                                    <label for="edit_name" class="block text-sm font-medium text-gray-700 mb-1">Plant Name</label>
                                    <input type="text" id="edit_name" name="name" value="${plant.name}" required
                                        class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent">
                                </div>
                                
                                <div>
                                    <label for="edit_location" class="block text-sm font-medium text-gray-700 mb-1">Location</label>
                                    <input type="text" id="edit_location" name="location" value="${plant.location}" required
                                        class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent">
                                </div>
                                
                                <div>
                                    <label for="edit_type" class="block text-sm font-medium text-gray-700 mb-1">Plant Type</label>
                                    <select id="edit_type" name="type" required
                                        class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent">
                                        <option value="solar" ${plant.type === 'solar' ? 'selected' : ''}>Solar</option>
                                        <option value="wind" ${plant.type === 'wind' ? 'selected' : ''}>Wind</option>
                                        <option value="both" ${plant.type === 'both' ? 'selected' : ''}>Both (Solar & Wind)</option>
                                    </select>
                                </div>
                                
                                <div>
                                    <label for="edit_threshold_value" class="block text-sm font-medium text-gray-700 mb-1">Threshold Value (kWh)</label>
                                    <input type="number" id="edit_threshold_value" name="threshold_value" step="0.01" min="0" value="${plant.threshold_value}" required
                                        class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent">
                                </div>
                                
                                <div class="flex justify-end pt-4">
                                    <button type="button" id="cancel-edit" class="bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded-lg mr-2">
                                        Cancel
                                    </button>
                                    <button type="submit" class="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg">
                                        Save Changes
                                    </button>
                                </div>
                            `;
                            
                            // Re-add event listener to cancel button
                            document.getElementById('cancel-edit').addEventListener('click', () => {
                                editPlantModal.classList.add('hidden');
                            });
                        } else {
                            alert('Error loading plant data: ' + data.message);
                            editPlantModal.classList.add('hidden');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('An error occurred while loading plant data.');
                        editPlantModal.classList.add('hidden');
                    });
            });
        });
        
        if (closeEditModal) {
            closeEditModal.addEventListener('click', () => {
                editPlantModal.classList.add('hidden');
            });
        }
        
        if (cancelEdit) {
            cancelEdit.addEventListener('click', () => {
                editPlantModal.classList.add('hidden');
            });
        }
    }
    
    // Delete Plant Modal Functionality
    const deleteBtns = document.querySelectorAll('.delete-plant-btn');
    const deletePlantModal = document.getElementById('delete-plant-modal');
    const closeDeleteModal = document.getElementById('close-delete-modal');
    const cancelDelete = document.getElementById('cancel-delete');
    const deletePlantIdInput = document.getElementById('delete_plant_id');
    
    if (deleteBtns.length && deletePlantModal && deletePlantIdInput) {
        deleteBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const plantId = btn.getAttribute('data-plant-id');
                
                // Set the plant ID in the form
                deletePlantIdInput.value = plantId;
                
                // Show the modal
                deletePlantModal.classList.remove('hidden');
            });
        });
        
        if (closeDeleteModal) {
            closeDeleteModal.addEventListener('click', () => {
                deletePlantModal.classList.add('hidden');
            });
        }
        
        if (cancelDelete) {
            cancelDelete.addEventListener('click', () => {
                deletePlantModal.classList.add('hidden');
            });
        }
    }
}); 