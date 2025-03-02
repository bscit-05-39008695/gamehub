 #models.py
from datetime import datetime
from extensions import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    game_sessions = db.relationship('GameSession', backref='user', lazy=True)
    bet_history = db.relationship('BetHistory', backref='user', lazy=True)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # deposit, withdraw
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # pending, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Game(db.Model):
    __tablename__ = 'games'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    min_bet = db.Column(db.Float, default=0.0)
    max_bet = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    game_sessions = db.relationship('GameSession', backref='game', lazy=True)
    bet_history = db.relationship('BetHistory', backref='game', lazy=True)

class GameSession(db.Model):
    __tablename__ = 'game_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    multiplayer_id = db.Column(db.Integer, db.ForeignKey('multiplayer.id'), nullable=True)
    status = db.Column(db.String(20), nullable=False)  # active, completed, left
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    spin_and_win = db.relationship('SpinAndWin', backref='session', lazy=True)

class SpinAndWin(db.Model):
    __tablename__ = 'spin_and_win'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('game_sessions.id'), nullable=False)
    bet_amount = db.Column(db.Float, nullable=False)
    win_amount = db.Column(db.Float, nullable=False)
    result = db.Column(db.String(20), nullable=False)  # e.g., "2x", "5x", "0x"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Multiplayer(db.Model):
    __tablename__ = 'multiplayer'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, nullable=False)  # Creator's session
    max_players = db.Column(db.Integer, nullable=False)
    current_players = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # waiting, ready, active, completed, abandoned
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    game_sessions = db.relationship('GameSession', backref='multiplayer_game', lazy=True)
    russian_roulette = db.relationship('RussianRoulette', backref='multiplayer_game', lazy=True)

class RussianRoulette(db.Model):
    __tablename__ = 'russian_roulette'
    
    id = db.Column(db.Integer, primary_key=True)
    multiplayer_id = db.Column(db.Integer, db.ForeignKey('multiplayer.id'), nullable=False)
    bullet_position = db.Column(db.Integer, nullable=False)  # 1-6
    current_position = db.Column(db.Integer, nullable=False)  # Current chamber
    status = db.Column(db.String(20), nullable=False)  # active, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BetHistory(db.Model):
    __tablename__ = 'bet_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    bet_amount = db.Column(db.Float, nullable=False)
    win_amount = db.Column(db.Float, default=0.0)
    net_result = db.Column(db.Float, default=0.0)
    bet_type = db.Column(db.String(20), nullable=True)  # For different bet types in games
    status = db.Column(db.String(20), default='completed')  # active, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
