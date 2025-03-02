# app.py
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
import random
import json
from datetime import datetime, timedelta
import time
import threading
import queue
from extensions import db

# Load environment variables from .env file
load_dotenv()



def create_app():
    app = Flask(__name__)

    # PostgreSQL configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')  # Change in production
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

    # Initialize extensions with app
    db.init_app(app)
    
    # Import models here to avoid circular imports
    from models import User, Transaction, GameSession, Game, SpinAndWin, RussianRoulette, Multiplayer, BetHistory
    
    migrate = Migrate(app, db)  # Add Flask-Migrate
    bcrypt = Bcrypt(app)  # Add Flask-Bcrypt
    jwt = JWTManager(app)
    CORS(app)

    # Game event management (replacing SocketIO)
    game_events = {}  # Dictionary to store event queues for each game

    # Root route to check if API is running
    @app.route('/', methods=['GET'])
    def home():
        return jsonify({"message": "API is running"}), 200

    # Authentication routes
    @app.route('/register', methods=['POST'])
    def register():
        data = request.get_json()
       
        if not data or 'username' not in data or 'email' not in data or 'password' not in data:
            return jsonify({"msg": "Missing required fields"}), 400
       
        if User.query.filter_by(username=data['username']).first() or User.query.filter_by(email=data['email']).first():
            return jsonify({"msg": "Username or email already exists"}), 400
       
        new_user = User(
            username=data['username'],
            email=data['email']
        )
        # Use bcrypt to hash password
        new_user.password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
       
        db.session.add(new_user)
        db.session.commit()
       
        access_token = create_access_token(identity=new_user.id)
        return jsonify({"msg": "User created successfully", "access_token": access_token}), 201

    @app.route('/login', methods=['POST'])
    def login():
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({"msg": "Missing username or password"}), 400
       
        user = User.query.filter_by(username=data['username']).first()
       
        if not user or not bcrypt.check_password_hash(user.password, data['password']):
            return jsonify({"msg": "Invalid credentials"}), 401
       
        access_token = create_access_token(identity=user.id)
        return jsonify({"access_token": access_token}), 200

    # User profile and balance routes
    @app.route('/profile', methods=['GET'])
    @jwt_required()
    def get_profile():
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"msg": "User not found"}), 404
       
        return jsonify({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "balance": user.balance,
            "created_at": user.created_at.isoformat()
        }), 200

    @app.route('/deposit', methods=['POST'])
    @jwt_required()
    def deposit():
        user_id = str(get_jwt_identity())  
        data = request.get_json()
    
        if not data or 'amount' not in data:
            return jsonify({"msg": "Missing amount"}), 400
    
        try:
            amount = float(data.get('amount', 0))  # Convert to float
        except ValueError:
            return jsonify({"msg": "Invalid amount format"}), 400
    
        if amount <= 0:
            return jsonify({"msg": "Invalid amount"}), 400
    
        user = User.query.get(user_id)
    
        if not user:
            return jsonify({"msg": "User not found"}), 404
    
        user.balance += amount
    
        transaction = Transaction(
            user_id=user_id,
            type='deposit',
            amount=amount,
            status='completed'
        )
    
        db.session.add(transaction)
        db.session.commit()
    
        return jsonify({"msg": "Deposit successful", "new_balance": user.balance}), 200

    @app.route('/api/withdraw', methods=['POST'])
    @jwt_required()
    def withdraw():
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'amount' not in data:
            return jsonify({"msg": "Missing amount"}), 400
            
        amount = data.get('amount', 0)
       
        if amount <= 0:
            return jsonify({"msg": "Invalid amount"}), 400
       
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"msg": "User not found"}), 404
       
        if user.balance < amount:
            return jsonify({"msg": "Insufficient balance"}), 400
       
        user.balance -= amount
       
        transaction = Transaction(
            user_id=user_id,
            type='withdraw',
            amount=amount,
            status='completed'
        )
       
        db.session.add(transaction)
        db.session.commit()
       
        return jsonify({"msg": "Withdrawal successful", "new_balance": user.balance}), 200

    # Spin and Win game routes
    @app.route('/api/games/spin-and-win/play', methods=['POST'])
    @jwt_required()
    def play_spin_and_win():
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'bet_amount' not in data:
            return jsonify({"msg": "Missing bet amount"}), 400
            
        bet_amount = data.get('bet_amount', 0)
       
        if bet_amount <= 0:
            return jsonify({"msg": "Invalid bet amount"}), 400
       
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"msg": "User not found"}), 404
       
        if user.balance < bet_amount:
            return jsonify({"msg": "Insufficient balance"}), 400
       
        # Create game session
        game = Game.query.filter_by(name='Spin and Win').first()
        
        if not game:
            return jsonify({"msg": "Game not found"}), 404
            
        session = GameSession(
            user_id=user_id,
            game_id=game.id,
            status='active'
        )
        db.session.add(session)
        db.session.flush()
       
        # Determine result (simplified example)
        segments = [
            {'value': 0, 'probability': 0.6},  # Lose
            {'value': bet_amount, 'probability': 0.2},  # Break even
            {'value': bet_amount * 2, 'probability': 0.15},  # 2x
            {'value': bet_amount * 5, 'probability': 0.05}  # 5x
        ]
       
        # Weighted random choice
        rand_val = random.random()
        cumulative_prob = 0
        win_amount = 0
       
        for segment in segments:
            cumulative_prob += segment['probability']
            if rand_val <= cumulative_prob:
                win_amount = segment['value']
                break
       
        # Create spin and win record
        spin = SpinAndWin(
            session_id=session.id,
            bet_amount=bet_amount,
            win_amount=win_amount,
            result=f"{win_amount / bet_amount if bet_amount > 0 else 0}x"
        )
       
        # Create bet history
        bet = BetHistory(
            user_id=user_id,
            game_id=game.id,
            bet_amount=bet_amount,
            win_amount=win_amount,
            net_result=win_amount - bet_amount
        )
       
        # Update user balance
        user.balance = user.balance - bet_amount + win_amount
       
        # Update session status
        session.status = 'completed'
       
        db.session.add_all([spin, bet])
        db.session.commit()
       
        return jsonify({
            "result": spin.result,
            "win_amount": win_amount,
            "new_balance": user.balance
        }), 200

    # SSE endpoints to replace SocketIO functionality
    @app.route('/api/events/connect', methods=['GET'])
    @jwt_required()
    def connect_to_events():
        user_id = get_jwt_identity()
        
        def event_stream():
            # Create a queue for this user if it doesn't exist
            if user_id not in game_events:
                game_events[user_id] = queue.Queue()
                
            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connected', 'user_id': user_id})}\n\n"
            
            # Keep connection alive and send events as they occur
            while True:
                try:
                    # Non-blocking queue check with timeout
                    event = game_events[user_id].get(timeout=1)
                    yield f"data: {json.dumps(event)}\n\n"
                except queue.Empty:
                    # Send heartbeat
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    time.sleep(30)  # Heartbeat interval
                except Exception:
                    break
                    
        return Response(stream_with_context(event_stream()), 
                       mimetype="text/event-stream")

    # Function to broadcast event to all users in a game
    def broadcast_to_game(game_id, event_data):
        # Find all users in this game
        game_session = GameSession.query.filter_by(game_id=game_id).all()
        user_ids = [session.user_id for session in game_session]
        
        # Add event to each user's queue
        for user_id in user_ids:
            if user_id in game_events:
                game_events[user_id].put(event_data)

    # Russian Roulette (Multiplayer) game routes
    @app.route('/api/games/join', methods=['POST'])
    @jwt_required()
    def join_game():
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'game_id' not in data:
            return jsonify({"msg": "Missing game ID"}), 400
            
        game_id = data.get('game_id')
        
        # Check if game exists
        game = Game.query.get(game_id)
        if not game:
            return jsonify({"msg": "Game not found"}), 404
        
        # Get open multiplayer game or create new one
        multiplayer = Multiplayer.query.filter_by(
            game_id=game_id,
            status='waiting'
        ).first()
        
        if not multiplayer:
            # Create new multiplayer game
            game_session = GameSession(
                user_id=user_id,
                game_id=game_id,
                status='waiting'
            )
            db.session.add(game_session)
            db.session.flush()
            
            multiplayer = Multiplayer(
                session_id=game_session.id,
                max_players=6,  # For Russian Roulette
                current_players=1,
                status='waiting'
            )
            db.session.add(multiplayer)
            db.session.commit()
            
            # Notify about new game
            event_data = {
                'type': 'game_status',
                'game_id': multiplayer.id,
                'status': 'waiting',
                'players': 1,
                'max_players': multiplayer.max_players
            }
        else:
            # Join existing multiplayer game
            multiplayer.current_players += 1
            
            if multiplayer.current_players >= multiplayer.max_players:
                multiplayer.status = 'ready'
                
            db.session.commit()
            
            # Notify about updated game status
            event_data = {
                'type': 'game_status',
                'game_id': multiplayer.id,
                'status': multiplayer.status,
                'players': multiplayer.current_players,
                'max_players': multiplayer.max_players
            }
            
            # Start game if ready
            if multiplayer.status == 'ready':
                start_russian_roulette(multiplayer.id, game_id)
        
        # Add user to game tracking
        game_session = GameSession(
            user_id=user_id,
            game_id=game_id,
            multiplayer_id=multiplayer.id,
            status='active'
        )
        db.session.add(game_session)
        db.session.commit()
        
        # Broadcast event
        broadcast_to_game(game_id, event_data)
        
        return jsonify({
            'game_id': multiplayer.id,
            'status': multiplayer.status,
            'players': multiplayer.current_players,
            'max_players': multiplayer.max_players
        }), 200

    def start_russian_roulette(multiplayer_id, game_id):
        # Get the multiplayer game
        multiplayer = Multiplayer.query.get(multiplayer_id)
        
        # Mark game as started
        multiplayer.status = 'active'
        db.session.commit()
        
        # Initialize the Russian Roulette game
        bullet_position = random.randint(1, 6)  # Random position for the bullet
        current_position = 1
        
        roulette = RussianRoulette(
            multiplayer_id=multiplayer_id,
            bullet_position=bullet_position,
            current_position=current_position,
            status='active'
        )
        db.session.add(roulette)
        db.session.commit()
        
        # Notify all players that game has started
        event_data = {
            'type': 'game_started',
            'game_id': multiplayer_id,
            'roulette_id': roulette.id
        }
        broadcast_to_game(game_id, event_data)

    @app.route('/api/games/place-bet', methods=['POST'])
    @jwt_required()
    def place_bet():
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'roulette_id' not in data or 'bet_amount' not in data or 'bet_type' not in data:
            return jsonify({"msg": "Missing required fields"}), 400
            
        roulette_id = data.get('roulette_id')
        bet_amount = data.get('bet_amount')
        bet_type = data.get('bet_type')  # 'survival' or 'elimination'
        
        if bet_type not in ['survival', 'elimination']:
            return jsonify({"msg": "Invalid bet type"}), 400
        
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"msg": "User not found"}), 404
            
        if user.balance < bet_amount:
            return jsonify({
                'status': 'error',
                'message': 'Insufficient balance'
            }), 400
        
        # Record the bet
        roulette = RussianRoulette.query.get(roulette_id)
        
        if not roulette:
            return jsonify({"msg": "Roulette game not found"}), 404
            
        multiplayer = Multiplayer.query.get(roulette.multiplayer_id)
        
        # Find game_id from an active session
        game_session = GameSession.query.filter_by(
            multiplayer_id=multiplayer.id,
            status='active'
        ).first()
        
        if not game_session:
            return jsonify({"msg": "No active game session found"}), 404
            
        game_id = game_session.game_id
        
        bet = BetHistory(
            user_id=user_id,
            game_id=game_id,
            bet_amount=bet_amount,
            bet_type=bet_type,
            status='active'
        )
        db.session.add(bet)
        
        # Deduct balance
        user.balance -= bet_amount
        db.session.commit()
        
        # Prepare response
        response = {
            'status': 'success',
            'bet_id': bet.id,
            'new_balance': user.balance
        }
        
        # Broadcast event to all players
        event_data = {
            'type': 'bet_placed',
            'user_id': user_id,
            'bet_type': bet_type,
            'bet_amount': bet_amount
        }
        broadcast_to_game(game_id, event_data)
        
        return jsonify(response), 200

    @app.route('/api/games/pull-trigger', methods=['POST'])
    @jwt_required()
    def pull_trigger():
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'roulette_id' not in data:
            return jsonify({"msg": "Missing roulette ID"}), 400
            
        roulette_id = data.get('roulette_id')
        
        roulette = RussianRoulette.query.get(roulette_id)
        
        if not roulette:
            return jsonify({"msg": "Roulette game not found"}), 404
            
        multiplayer = Multiplayer.query.get(roulette.multiplayer_id)
        
        # Find game_id from an active session
        game_session = GameSession.query.filter_by(
            multiplayer_id=multiplayer.id,
            status='active'
        ).first()
        
        if not game_session:
            return jsonify({"msg": "No active game session found"}), 404
            
        game_id = game_session.game_id
        
        # Check if it's a hit
        is_hit = roulette.current_position == roulette.bullet_position
        
        # Update position
        roulette.current_position += 1
        
        if is_hit or roulette.current_position > 6:
            # Game over
            roulette.status = 'completed'
            multiplayer.status = 'completed'
            
            # Update all related game sessions
            GameSession.query.filter_by(
                multiplayer_id=multiplayer.id,
                status='active'
            ).update({'status': 'completed'})
            
            # Process all bets
            bets = BetHistory.query.filter_by(
                game_id=game_id,
                status='active'
            ).all()
            
            for bet in bets:
                if (bet.bet_type == 'survival' and not is_hit) or (bet.bet_type == 'elimination' and is_hit):
                    # Winner - calculate payout based on odds and number of players
                    odds_multiplier = 2.0  # Simplified example
                    win_amount = bet.bet_amount * odds_multiplier
                    
                    bet.win_amount = win_amount
                    bet.net_result = win_amount - bet.bet_amount
                    
                    # Update user balance
                    better = User.query.get(bet.user_id)
                    if better:
                        better.balance += win_amount
                else:
                    # Loser
                    bet.win_amount = 0
                    bet.net_result = -bet.bet_amount
                
                bet.status = 'completed'
            
            db.session.commit()
            
            # Notify all players
            event_data = {
                'type': 'game_result',
                'is_hit': is_hit,
                'position': roulette.current_position - 1,
                'bullet_position': roulette.bullet_position,
                'game_over': True
            }
        else:
            # Continue game
            db.session.commit()
            
            # Notify all players
            event_data = {
                'type': 'trigger_result',
                'is_hit': is_hit,
                'position': roulette.current_position - 1,
                'game_over': False
            }
        
        broadcast_to_game(game_id, event_data)
        
        return jsonify(event_data), 200

    @app.route('/api/games/leave', methods=['POST'])
    @jwt_required()
    def leave_game():
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'game_id' not in data:
            return jsonify({"msg": "Missing game ID"}), 400
            
        game_id = data.get('game_id')
        
        # Find and update the user's game session
        game_session = GameSession.query.filter_by(
            user_id=user_id,
            game_id=game_id,
            status='active'
        ).first()
        
        if game_session:
            game_session.status = 'left'
            
            # If this is a multiplayer game, update player count
            if game_session.multiplayer_id:
                multiplayer = Multiplayer.query.get(game_session.multiplayer_id)
                if multiplayer and multiplayer.status != 'completed':
                    multiplayer.current_players -= 1
                    
                    # If no players left, mark game as abandoned
                    if multiplayer.current_players <= 0:
                        multiplayer.status = 'abandoned'
            
            db.session.commit()
            
            # Notify others that player has left
            event_data = {
                'type': 'player_left',
                'user_id': user_id
            }
            broadcast_to_game(game_id, event_data)
            
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'No active game session found'}), 404

    # Game stats and history routes
    @app.route('/api/history', methods=['GET'])
    @jwt_required()
    def get_history():
        user_id = get_jwt_identity()
        
        bets = BetHistory.query.filter_by(user_id=user_id).order_by(BetHistory.created_at.desc()).limit(50).all()
        
        history = []
        for bet in bets:
            game = Game.query.get(bet.game_id)
            if game:
                history.append({
                    'id': bet.id,
                    'game': game.name,
                    'bet_amount': bet.bet_amount,
                    'win_amount': bet.win_amount,
                    'net_result': bet.net_result,
                    'created_at': bet.created_at.isoformat()
                })
        
        return jsonify(history), 200

    @app.route('/api/stats', methods=['GET'])
    @jwt_required()
    def get_stats():
        user_id = get_jwt_identity()
        
        # Get overall stats
        bets = BetHistory.query.filter_by(user_id=user_id).all()
        
        total_bets = len(bets)
        total_wagered = sum(bet.bet_amount for bet in bets)
        total_won = sum(bet.win_amount for bet in bets)
        net_profit = total_won - total_wagered
        
        # Get stats by game
        games = Game.query.all()
        games_stats = []
        
        for game in games:
            game_bets = [bet for bet in bets if bet.game_id == game.id]
            
            if game_bets:
                game_total_bets = len(game_bets)
                game_total_wagered = sum(bet.bet_amount for bet in game_bets)
                game_total_won = sum(bet.win_amount for bet in game_bets)
                game_net_profit = game_total_won - game_total_wagered
                
                games_stats.append({
                    'game': game.name,
                    'total_bets': game_total_bets,
                    'total_wagered': game_total_wagered,
                    'total_won': game_total_won,
                    'net_profit': game_net_profit
                })
        
        return jsonify({
            'overall': {
                'total_bets': total_bets,
                'total_wagered': total_wagered,
                'total_won': total_won,
                'net_profit': net_profit
            },
            'by_game': games_stats
        }), 200

    # Add error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found", "message": "The requested URL was not found on the server"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error", "message": "The server encountered an internal error"}), 500

    # Command to initialize tables when needed (not used with migrations)
    @app.cli.command("init-db")
    def init_db_command():
        """Clear existing data and create new tables."""
        db.create_all()
        print("Initialized the database.")
        
    return app

# This is the app instance that will be used by Flask CLI
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)