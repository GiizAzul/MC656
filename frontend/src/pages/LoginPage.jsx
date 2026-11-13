import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/AuthPage.css';

export default function LoginPage({ onLoginSuccess }) {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [senha, setSenha] = useState('');
  const [erro, setErro] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErro('');

    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('senha', senha);

    const res = await fetch('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString(),
      redirect: 'manual',
    });

    if (res.status === 302 || res.type === 'opaqueredirect' || res.redirected) {
      if (onLoginSuccess) await onLoginSuccess();
      navigate('/dashboard');
    } else {
      setErro('Erro: Usuário/RA não encontrado ou senha incorreta.');
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <div className="auth-header">
          <h1>Sistema de Votação</h1>
          <p>Entre com seu Username ou RA (Unicamp)</p>
        </div>

        {erro && <div className="alert-banner alert-error">{erro}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="login-username">Identificação (RA/Usuário)</label>
            <input
              id="login-username"
              type="text"
              className="form-control"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="login-senha">Senha</label>
            <input
              id="login-senha"
              type="password"
              className="form-control"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="btn-primary" style={{ width: '100%' }}>
            Entrar
          </button>
        </form>

        <div className="auth-footer">
          Não possui conta ou quer vincular outro escopo? <Link to="/cadastro">Cadastre-se</Link>
        </div>
      </div>
    </div>
  );
}