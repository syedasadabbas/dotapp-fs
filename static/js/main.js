// Navbar Scroll Effect
window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
});

// Auth Modal
const modal = document.getElementById('authModal');
const loginBtn = document.querySelector('.login-btn');
const signupBtn = document.querySelector('.signup-btn');
const closeModal = document.querySelector('.close-modal');
const tabBtns = document.querySelectorAll('.tab-btn');
const roleBtns = document.querySelectorAll('.role-btn');

// Open modal
loginBtn.addEventListener('click', () => {
    modal.style.display = 'block';
    document.querySelector('[data-tab="login"]').click();
});

signupBtn.addEventListener('click', () => {
    modal.style.display = 'block';
    document.querySelector('[data-tab="signup"]').click();
});

// Close modal
closeModal.addEventListener('click', () => {
    modal.style.display = 'none';
});

window.addEventListener('click', (e) => {
    if (e.target === modal) {
        modal.style.display = 'none';
    }
});

// Tab switching
tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        // Remove active class from all tabs
        tabBtns.forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
        
        // Add active class to clicked tab
        btn.classList.add('active');
        document.getElementById(btn.dataset.tab).classList.add('active');
    });
});

// Role switching
roleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const form = btn.closest('form');
        const roleSpecificFields = form.querySelectorAll('.role-specific-fields');
        
        // Update active role button
        btn.parentElement.querySelectorAll('.role-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Show/hide role-specific fields
        roleSpecificFields.forEach(fields => {
            fields.classList.add('hidden');
            if (fields.classList.contains(btn.dataset.role)) {
                fields.classList.remove('hidden');
            }
        });
    });
});

// Form submission
document.getElementById('loginForm').addEventListener('submit', (e) => {
    e.preventDefault();
    // Add login logic here
    console.log('Login submitted');
});

document.getElementById('signupForm').addEventListener('submit', (e) => {
    e.preventDefault();
    // Add signup logic here
    console.log('Signup submitted');
});

// Circular Course Display
const courses = document.querySelectorAll('.course-item');
const totalCourses = courses.length;
const radius = 200; // Adjust based on your needs

courses.forEach((course, index) => {
    const angle = (index / totalCourses) * 2 * Math.PI;
    const x = radius * Math.cos(angle);
    const y = radius * Math.sin(angle);
    
    course.style.left = `calc(50% + ${x}px - 50px)`;
    course.style.top = `calc(50% + ${y}px - 50px)`;
});// Auth Page Functionality
document.addEventListener('DOMContentLoaded', () => {
    // Role Selector
    const roleBtns = document.querySelectorAll('.role-btn');
    const roleSpecificSections = document.querySelectorAll('.role-specific');

    roleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all buttons
            roleBtns.forEach(b => b.classList.remove('active'));
            // Hide all role-specific sections
            roleSpecificSections.forEach(section => section.classList.remove('active'));
            
            // Add active class to clicked button
            btn.classList.add('active');
            // Show corresponding role-specific section
            document.querySelector(`.role-specific.${btn.dataset.role}`).classList.add('active');
        });
    });

    // Form Validation
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');

    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            // Add login logic here
            console.log('Login submitted');
            window.location.href = 'dashboard-learner.html';
        });
    }

    if (signupForm) {
        signupForm.addEventListener('submit', (e) => {
            e.preventDefault();
            // Add signup logic here
            console.log('Signup submitted');
            window.location.href = 'dashboard-learner.html';
        });
    }
});

//image upload 
document.addEventListener("DOMContentLoaded", function() {
    document.getElementById('image-input').addEventListener('change', function(event) {
        var file = event.target.files[0];

        if (file) {
            var reader = new FileReader();
            reader.onload = function(e) {
                var previewImage = document.getElementById('image-preview');
                var previewContainer = document.getElementById('image-preview-container');

                previewImage.src = e.target.result;
                previewContainer.style.display = "block"; // ✅ Show the image preview
            };
            reader.readAsDataURL(file);
        }
    });
});

