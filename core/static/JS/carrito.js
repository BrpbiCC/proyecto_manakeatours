// static/js/carrito.js

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
                    const startDate = new Date(item.fechas[0] + 'T12:00:00').toLocaleDateString('es-CL');
                    const endDate = new Date(item.fechas[1] + 'T12:00:00').toLocaleDateString('es-CL');
                    itemDetails += `<p>Fechas: ${startDate} al ${endDate} (${item.noches} noches)</p>`;
                } else if (item.tipoServicio === 'Actividad' && item.fechas && item.fechas.length === 1) {
                    const activityDate = new Date(item.fechas[0] + 'T12:00:00').toLocaleDateString('es-CL');
                    itemDetails += `<p>Fecha: ${activityDate}</p>`;
                } else if (item.tipoServicio === 'Gastronomia' && item.fechas && item.fechas.length === 1) {
                    const gastronomyDate = new Date(item.fechas[0] + 'T12:00:00').toLocaleDateString('es-CL');
                    itemDetails += `<p>Fecha: ${gastronomyDate}</p>`;
                }
                // Display number of people ONLY for Actividad and Gastronomia
                if (item.cantidadPersonas && (item.tipoServicio.toLowerCase() === 'actividad' || item.tipoServicio.toLowerCase() === 'gastronomia')) {
                    itemDetails += `<p>Personas: ${item.cantidadPersonas}</p>`;
                }
                
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
                loadCart(); // Load and render cart when opening
            }
        });
    }

    // Close cart when clicking outside
    document.addEventListener('click', function(event) {
        if (carritoDesplegable && carritoTrigger &&
            !carritoDesplegable.contains(event.target) && 
            !carritoTrigger.contains(event.target) && 
            carritoDesplegable.classList.contains('abierto')) {
            
            carritoDesplegable.classList.remove('abierto');
            mainContent.classList.remove('carrito-abierto');
        }
    });

    // --- EXPOSE addToCartFromDetail TO THE GLOBAL WINDOW OBJECT ---
    // This function will be called from detail pages (e.g., detalle_hospedaje.html)
    window.addToCartFromDetail = function({ servicio_id, nombre_servicio, tipo_servicio, precio_base, fecha_inicio, fecha_fin, cantidad_dias, cantidad_personas }) {
        console.log("addToCartFromDetail llamado con:", { servicio_id, nombre_servicio, tipo_servicio, precio_base, fecha_inicio, fecha_fin, cantidad_dias, cantidad_personas });
        
        let subtotal = 0;
        let noches = 0;
        let selectedDatesArray = [];

        if (tipo_servicio.toLowerCase() === 'hospedaje') {
            selectedDatesArray = [fecha_inicio, fecha_fin];
            noches = cantidad_dias;
            subtotal = noches * precio_base; // cantidad_personas for hospedaje is fixed at 1
        } else if (tipo_servicio.toLowerCase() === 'actividad' || tipo_servicio.toLowerCase() === 'gastronomia') {
            selectedDatesArray = [fecha_inicio];
            subtotal = precio_base * cantidad_personas;
            noches = 0; // Not applicable for these types
        }

        const newItem = {
            id: servicio_id,
            nombre: nombre_servicio,
            tipoServicio: tipo_servicio,
            fechas: selectedDatesArray,
            noches: noches,
            subtotal: subtotal,
            // Only include cantidadPersonas if it's relevant for the service type
            cantidadPersonas: (tipo_servicio.toLowerCase() === 'actividad' || tipo_servicio.toLowerCase() === 'gastronomia') ? cantidad_personas : undefined
        };

        let cartItems = JSON.parse(sessionStorage.getItem('cartItems')) || [];
        cartItems.push(newItem);
        saveCart(cartItems);
        renderCart(cartItems); // Re-render the cart after adding

        Swal.fire({
            icon: 'success',
            title: '¡Añadido al carrito!',
            text: `${nombre_servicio} ha sido añadido.`,
            showConfirmButton: false,
            timer: 1500
        });
    };

    // --- EXPOSE updateCartDisplay TO THE GLOBAL WINDOW OBJECT ---
    // This allows other scripts to request a cart update (e.g., after an item is removed from full cart page)
    window.updateCartDisplay = function() {
        loadCart(); // Simply call loadCart which will re-render the display
    };

    // Initial load of the cart when the page loads
    loadCart();
});