import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/Navbar.css';

export default function Navbar({ usuario, onLogout }) {
  const escopos = usuario?.escopo ? usuario.escopo.split(',') : [];

  return (
    <header className="top-navbar">
      <Link to={usuario ? '/dashboard' : '/'} className="navbar-brand">
        <span>🗳️ Sistema de Votação Multi-Escopo</span>
      </Link>

      {usuario && (
        <>
          <div className="navbar-scopes">
            {escopos.map((esc) => (
              <span key={esc} className="scope-pill">
                {esc}
              </span>
            ))}
          </div>
          <div className="navbar-actions">
            <span className="navbar-user">
              Olá, <strong>{usuario.nome_real}</strong> ({usuario.username})
            </span>
            <a href="/logout" onClick={onLogout} className="btn-logout">
              Sair
            </a>
          </div>
        </>
      )}
    </header>
  );
}