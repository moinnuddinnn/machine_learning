/* General Styles */
body {
    margin: 0;
    padding: 0;
    font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #000000, #000000);
    color: white;
    height: 100vh;
    display: flex;
    flex-direction: column;
}

/* Navbar */
.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    background-color: rgba(73, 73, 73, 0.8);
    backdrop-filter: blur(10px);
    position: sticky;
    top: 0;
}

.navbar h1 {
    font-size: 1.8rem;
    font-weight: bold;
    color: #009233;
    margin: 0;
}

.nav-buttons a {
    text-decoration: none;
    color: white;
    margin-left: 1.2rem;
    font-weight: 500;
    transition: color 0.3s, transform 0.2s;
}

.nav-buttons a:hover {
    color: #009233;
    transform: scale(1.05);
}

/* Content */
.content {
    text-align: center;
    margin: auto;
    padding: 2rem;
}

.content h2 {
    font-size: 2.5rem;
    margin-bottom: 1rem;
    color: #009233;
}

.content p {
    font-size: 1.2rem;
    line-height: 1.6;
    max-width: 700px;
    margin: auto;
    color: #e0e0e0;
}

/* Button Style (Optional if you want CTA) */
.button {
    display: inline-block;
    margin-top: 1.5rem;
    padding: 0.8rem 1.5rem;
    background: #1DB954;
    color: white;
    font-size: 1rem;
    font-weight: bold;
    border-radius: 25px;
    text-decoration: none;
    transition: background 0.3s, transform 0.2s;
}

.button:hover {
    background: #1aa34a;
    transform: translateY(-3px);
}
