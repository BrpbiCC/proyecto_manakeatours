document.addEventListener('DOMContentLoaded', function() {
    const carritoDesplegable = document.getElementById('carrito-desplegable');
    const carritoTrigger = document.querySelector('.carrito-trigger');
    const mainContent = document.getElementById('main-content');
    const itemsCarritoDiv = document.getElementById('items-carrito');
    const totalCarritoSpan = document.getElementById('total-carrito');

    // Function to load cart items from sessionStorage
    function loadCart() {
        const cartItems = JSON.parse(sessionStorage.getItem('cartItems')) || [];
        renderCart(cartItems);
    }

    // Function to save cart items to sessionStorage
    function saveCart(cartItems) {
        sessionStorage.setItem('cartItems', JSON.stringify(cartItems));
    }

    // Function to render cart items in the dropdown
    function renderCart(cartItems) {
        itemsCarritoDiv.innerHTML = ''; // Clear current items
        let total = 0;

        if (cartItems.length === 0) {
            itemsCarritoDiv.innerHTML = '<p>El carrito está vacío.</p>';
        } else {
            cartItems.forEach((item, index) => {
                const itemDiv = document.createElement('div');
                itemDiv.classList.add('carrito-item');
                let itemDetails = `
                    <p><strong>${item.nombre}</strong></p>
                    <p>Tipo: ${item.tipoServicio}</p>
                `;
                if (item.tipoServicio === 'Hospedaje' && item.fechas && item.fechas.length === 2) {
                    const startDate = new Date(item.fechas[0]).toLocaleDateString('es-CL');
                    const endDate = new Date(item.fechas[1]).toLocaleDateString('es-CL');
                    itemDetails += `<p>Fechas: ${startDate} al ${endDate} (${item.noches} noches)</p>`;
                } else if (item.tipoServicio === 'Actividad' && item.fechas && item.fechas.length === 1) {
                    const activityDate = new Date(item.fechas[0]).toLocaleDateString('es-CL');
                    itemDetails += `<p>Fecha: ${activityDate}</p>`;
                } else if (item.tipoServicio === 'Gastronomia' && item.fechas && item.fechas.length === 1) {
                    const gastronomyDate = new Date(item.fechas[0]).toLocaleDateString('es-CL');
                    itemDetails += `<p>Fecha: ${gastronomyDate}</p>`;
                }
                // Display number of people only for Actividad and Gastronomia
                if (item.cantidadPersonas && (item.tipoServicio === 'Actividad' || item.tipoServicio === 'Gastronomia')) {
                    itemDetails += `<p>Personas: ${item.cantidadPersonas}</p>`;
                }
                // REMOVED: The condition that added "Adultos: X" for Hospedaje.

                itemDetails += `<p>Subtotal: $${item.subtotal.toFixed(2)}</p>`;
                itemDiv.innerHTML = itemDetails;

                const removeButton = document.createElement('button');
                removeButton.classList.add('btn', 'btn-danger', 'btn-sm', 'remove-item-btn');
                removeButton.textContent = 'Eliminar';
                removeButton.addEventListener('click', () => {
                    removeItemFromCart(index);
                });
                itemDiv.appendChild(removeButton);
                itemsCarritoDiv.appendChild(itemDiv);
                total += item.subtotal;
            });
        }
        totalCarritoSpan.textContent = total.toFixed(2);
    }

    // Function to remove an item from the cart
    function removeItemFromCart(index) {
        let cartItems = JSON.parse(sessionStorage.getItem('cartItems')) || [];
        cartItems.splice(index, 1);
        saveCart(cartItems);
        renderCart(cartItems);
    }

    // Toggle cart visibility
    if (carritoTrigger && carritoDesplegable && mainContent) {
        carritoTrigger.addEventListener('click', function(event) {
            event.preventDefault();
            carritoDesplegable.classList.toggle('abierto');
            mainContent.classList.toggle('carrito-abierto');
            if (carritoDesplegable.classList.contains('abierto')) {
                loadCart();
            }
        });
    }

    // Add to cart functionality
    document.querySelectorAll('.add-to-cart-btn').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            const form = this.closest('.reservation-form');
            const serviceId = form.dataset.serviceId;
            const serviceType = form.dataset.serviceType;
            const pricePerPerson = parseFloat(form.dataset.pricePerPerson); 
            const serviceName = form.closest('.card').querySelector('.card-title').textContent;
            const dateInput = form.querySelector('.date-input');
            const numPeopleInput = form.querySelector('.num-personas-input');
            // For Hospedaje, numberOfPeople will be 1 as per the HTML change.
            // For Actividad/Gastronomia, it will read the value from .num-personas-input if present.
            const numberOfPeople = numPeopleInput ? parseInt(numPeopleInput.value) : 1;

            const flatpickrInstance = dateInput._flatpickr;

            if (!flatpickrInstance || flatpickrInstance.selectedDates.length === 0) {
                alert('Por favor, selecciona al menos una fecha.');
                return;
            }

            let subtotal = 0;
            let noches = 0;
            let selectedDates = flatpickrInstance.selectedDates.map(date => date.toISOString().split('T')[0]); 

            if (serviceType.toLowerCase() === 'hospedaje') {
                if (selectedDates.length === 2) {
                    const startDate = new Date(selectedDates[0]);
                    const endDate = new Date(selectedDates[1]);
                    const diffTime = endDate.getTime() - startDate.getTime(); 
                    const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24)); 
                    noches = diffDays;
                    subtotal = noches * pricePerPerson * numberOfPeople; 
                } else if (selectedDates.length === 1) {
                    noches = 1; 
                    subtotal = pricePerPerson * numberOfPeople; 
                }
            } else if (serviceType.toLowerCase() === 'actividad' || serviceType.toLowerCase() === 'gastronomia') {
                subtotal = pricePerPerson * numberOfPeople;
                noches = 0;
            }

            const newItem = {
                id: serviceId,
                nombre: serviceName,
                tipoServicio: serviceType, 
                fechas: selectedDates,
                noches: noches, 
                subtotal: subtotal,
                cantidadPersonas: numberOfPeople 
            };

            let cartItems = JSON.parse(sessionStorage.getItem('cartItems')) || [];
            cartItems.push(newItem);
            saveCart(cartItems);
            renderCart(cartItems); 
            alert(`${serviceName} ha sido añadido al carrito.`);
        });
    });

    // Initial load of the cart when the page loads
    loadCart();

    // === Flatpickr Initialization and Price Display Logic ===
    const flatpickrInstances = {};

    const rangePickerOptions = {
        mode: "range",
        minDate: "today",
        dateFormat: "Y-m-d",
        locale: "es",
        onChange: function(selectedDates, dateStr, instance) {
            const cardBody = instance.element.closest('.card-body');
            const priceDisplay = cardBody.querySelector('[id^="price-display-"]');
            const form = instance.element.closest('.reservation-form');
            const serviceType = form.dataset.serviceType; 
            // For Hospedaje, numberOfPeople will be fixed at 1 as per your request
            const numberOfPeople = 1; 

            if (serviceType.toLowerCase() === 'hospedaje') {
                let servicePricePerNight = parseFloat(form.dataset.pricePerPerson);
                
                if (selectedDates.length === 2) {
                    const startDate = selectedDates[0];
                    const endDate = selectedDates[1];
                    const diffTime = endDate.getTime() - startDate.getTime(); 
                    const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24)); 

                    const estimatedPrice = (diffDays * servicePricePerNight * numberOfPeople).toFixed(2);
                    priceDisplay.innerText = `Noches: ${diffDays} (${startDate.toLocaleDateString('es-CL')} al ${endDate.toLocaleDateString('es-CL')}) - Precio estimado: $${estimatedPrice}`;
                } else if (selectedDates.length === 1) {
                    const estimatedPrice = (servicePricePerNight * numberOfPeople).toFixed(2);
                    priceDisplay.innerText = `Noches: 1 (${selectedDates[0].toLocaleDateString('es-CL')}) - Precio estimado: $${estimatedPrice}`;
                } else {
                    priceDisplay.innerText = `Precio estimado: $0.00`;
                }
            }
        }
    };

    const singlePickerOptions = {
        mode: "single",
        minDate: "today",
        dateFormat: "Y-m-d",
        locale: "es",
        onChange: function(selectedDates, dateStr, instance) {
            const cardBody = instance.element.closest('.card-body');
            const priceDisplay = cardBody.querySelector('[id^="price-display-"]');
            const form = instance.element.closest('.reservation-form');
            const servicePrice = parseFloat(form.dataset.pricePerPerson);
            const numPeopleInput = form.querySelector('.num-personas-input');
            const numberOfPeople = numPeopleInput ? parseInt(numPeopleInput.value) : 1;

            if (selectedDates.length === 1) {
                const estimatedPrice = (servicePrice * numberOfPeople).toFixed(2); 
                const serviceType = form.dataset.serviceType;
                let dateLabel = 'Fecha seleccionada';
                if (serviceType.toLowerCase() === 'gastronomia') {
                    dateLabel = 'Fecha de reserva';
                }
                priceDisplay.innerText = `${dateLabel}: ${selectedDates[0].toLocaleDateString('es-CL')} - Personas: ${numberOfPeople} - Precio: $${estimatedPrice}`; 
            } else {
                const estimatedPrice = (servicePrice * numberOfPeople).toFixed(2); 
                const serviceType = form.dataset.serviceType;
                let label = 'Precio estimado';
                if (serviceType.toLowerCase() === 'gastronomia' || serviceType.toLowerCase() === 'actividad') {
                    label = 'Precio';
                }
                priceDisplay.innerText = `${label}: $${estimatedPrice}`;
            }
        }
    };

    document.querySelectorAll('.reservation-form').forEach(form => {
        const serviceType = form.dataset.serviceType;
        const dateInput = form.querySelector('input[type="text"][id^="fecha-reserva-"]');

        if (dateInput) {
            if (serviceType.toLowerCase() === 'hospedaje') {
                const instance = flatpickr(dateInput, rangePickerOptions);
                flatpickrInstances[dateInput.id] = instance;
            } else if (serviceType.toLowerCase() === 'actividad' || serviceType.toLowerCase() === 'gastronomia') {
                const instance = flatpickr(dateInput, singlePickerOptions);
                flatpickrInstances[dateInput.id] = instance;
            }
        }
    });

    document.querySelectorAll('.clear-flatpickr').forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.dataset.targetFlatpickr;
            if (flatpickrInstances[targetId]) {
                flatpickrInstances[targetId].clear(); 

                const form = this.closest('.reservation-form');
                const priceDisplay = form.querySelector('[id^="price-display-"]');
                const serviceType = form.dataset.serviceType;
                const servicePrice = parseFloat(form.dataset.pricePerPerson);
                const numPeopleInput = form.querySelector('.num-personas-input');
                const numberOfPeople = numPeopleInput ? parseInt(numPeopleInput.value) : 1;

                if (serviceType.toLowerCase() === 'hospedaje') {
                   priceDisplay.innerText = `Precio estimado: $0.00`;
                } else if (serviceType.toLowerCase() === 'actividad' || serviceType.toLowerCase() === 'gastronomia') {
                   priceDisplay.innerText = `Precio: $${(servicePrice * numberOfPeople).toFixed(2)}`;
                }
            }
        });
    });

    document.querySelectorAll('.num-personas-input').forEach(input => {
        input.addEventListener('change', function() {
            const form = this.closest('.reservation-form');
            const dateInput = form.querySelector('.date-input');
            const flatpickrInstance = dateInput._flatpickr;
            
            const serviceType = form.dataset.serviceType;
            const priceDisplay = form.querySelector('[id^="price-display-"]');
            const servicePrice = parseFloat(form.dataset.pricePerPerson);
            const numberOfPeople = parseInt(this.value) || 1; 
            
            if (flatpickrInstance && flatpickrInstance.selectedDates.length > 0) {
                flatpickrInstance.config.onChange(flatpickrInstance.selectedDates, flatpickrInstance.input.value, flatpickrInstance);
            } else {
                if (serviceType.toLowerCase() === 'actividad' || serviceType.toLowerCase() === 'gastronomia') {
                    priceDisplay.innerText = `Precio: $${(servicePrice * numberOfPeople).toFixed(2)}`;
                } else if (serviceType.toLowerCase() === 'hospedaje') {
                    priceDisplay.innerText = `Precio estimado: $0.00`;
                }
            }
        });
    });
});