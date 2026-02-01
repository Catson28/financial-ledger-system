#!/usr/bin/env python3
"""
Ledger System - Setup and Installation Script
==============================================
Automated setup for the Ledger / Accounting Engine.

This script will:
1. Check Python version
2. Create virtual environment
3. Install dependencies
4. Create configuration files
5. Initialize database
6. Create sample chart of accounts

Usage:
    python setup.py
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header(message):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(f"  {message}")
    print("=" * 80 + "\n")


def check_python_version():
    """Check if Python version is adequate."""
    print_header("Checking Python Version")
    
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ Error: Python 3.10 or higher required")
        sys.exit(1)
    
    print("✅ Python version OK")


def create_venv():
    """Create virtual environment."""
    print_header("Creating Virtual Environment")
    
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("⚠️  Virtual environment already exists")
        response = input("Recreate? (y/n): ").strip().lower()
        if response != 'y':
            print("Skipping venv creation")
            return
        
        import shutil
        shutil.rmtree(venv_path)
    
    print("Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
    print("✅ Virtual environment created")


def install_dependencies():
    """Install Python dependencies."""
    print_header("Installing Dependencies")
    
    # Determine pip path
    if sys.platform == "win32":
        pip_path = Path("venv/Scripts/pip")
    else:
        pip_path = Path("venv/bin/pip")
    
    if not pip_path.exists():
        print("❌ Error: Virtual environment not found")
        print("   Please activate virtual environment first")
        sys.exit(1)
    
    print("Installing requirements...")
    subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], check=True)
    print("✅ Dependencies installed")


def create_env_file():
    """Create .env file from template."""
    print_header("Creating Environment Configuration")
    
    env_file = Path(".env")
    
    if env_file.exists():
        print("⚠️  .env file already exists")
        response = input("Overwrite? (y/n): ").strip().lower()
        if response != 'y':
            print("Skipping .env creation")
            return
    
    template_file = Path(".env.template")
    
    if not template_file.exists():
        print("❌ Error: .env.template not found")
        sys.exit(1)
    
    # Copy template
    import shutil
    shutil.copy(template_file, env_file)
    
    print("✅ .env file created")
    print("\n⚠️  IMPORTANT: Edit .env file with your database credentials!")
    print("   Required: LEDGER_DB_URI")


def check_database_config():
    """Check if database is configured."""
    print_header("Checking Database Configuration")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    db_uri = os.getenv('LEDGER_DB_URI')
    
    if not db_uri or 'localhost' in db_uri or 'user:password' in db_uri:
        print("⚠️  Database not configured properly")
        print("   Please edit .env file with correct database credentials")
        print("   Example: LEDGER_DB_URI=mysql+pymysql://user:pass@host:3306/dbname")
        return False
    
    print(f"✅ Database configured: {db_uri.split('@')[1] if '@' in db_uri else 'configured'}")
    return True


def initialize_database():
    """Initialize database schema."""
    print_header("Initializing Database")
    
    if not check_database_config():
        print("Skipping database initialization")
        print("Please configure database and run: python ledger_admin_cli.py init --confirm")
        return
    
    response = input("Initialize database now? (y/n): ").strip().lower()
    if response != 'y':
        print("Skipping database initialization")
        return
    
    try:
        from ledger_engine import LedgerEngine
        
        print("Creating database tables...")
        ledger = LedgerEngine()
        print("✅ Database initialized successfully")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        print("   You can initialize manually later with:")
        print("   python ledger_admin_cli.py init --confirm")


def create_sample_accounts():
    """Create sample chart of accounts."""
    print_header("Creating Sample Chart of Accounts")
    
    response = input("Create sample accounts? (y/n): ").strip().lower()
    if response != 'y':
        print("Skipping sample accounts creation")
        return
    
    try:
        from ledger_engine import LedgerEngine, AccountDefinition, AccountType
        
        ledger = LedgerEngine()
        
        sample_accounts = [
            # Assets
            ("1000", "ATIVOS", AccountType.ASSET, None),
            ("1100", "Caixa e Bancos", AccountType.ASSET, "1000"),
            ("1200", "Contas a Receber", AccountType.ASSET, "1000"),
            
            # Liabilities
            ("2000", "PASSIVOS", AccountType.LIABILITY, None),
            ("2100", "Contas a Pagar", AccountType.LIABILITY, "2000"),
            ("2200", "Empréstimos", AccountType.LIABILITY, "2000"),
            
            # Equity
            ("3000", "PATRIMÔNIO LÍQUIDO", AccountType.EQUITY, None),
            ("3100", "Capital Social", AccountType.EQUITY, "3000"),
            
            # Revenue
            ("4000", "RECEITAS", AccountType.REVENUE, None),
            ("4100", "Receitas de Vendas", AccountType.REVENUE, "4000"),
            
            # Expenses
            ("5000", "DESPESAS", AccountType.EXPENSE, None),
            ("5100", "Custos de Vendas", AccountType.EXPENSE, "5000"),
            ("5200", "Despesas Administrativas", AccountType.EXPENSE, "5000"),
        ]
        
        print("Creating sample accounts...")
        for code, name, acc_type, parent in sample_accounts:
            account_def = AccountDefinition(
                account_code=code,
                account_name=name,
                account_type=acc_type,
                parent_account_code=parent,
                description=f"Conta de exemplo: {name}"
            )
            
            ledger.create_account(account_def, created_by="setup_script")
            print(f"  ✓ {code} - {name}")
        
        print("✅ Sample accounts created")
        
    except Exception as e:
        print(f"❌ Error creating sample accounts: {e}")


def show_next_steps():
    """Show next steps to user."""
    print_header("Setup Complete!")
    
    print("Next steps:\n")
    print("1. Activate virtual environment:")
    
    if sys.platform == "win32":
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    
    print("\n2. Review and edit .env file with your configuration")
    
    print("\n3. Run discovery tool to define your ledger:")
    print("   python ledger_discovery_tool.py")
    
    print("\n4. Use CLI to manage the ledger:")
    print("   python ledger_admin_cli.py --help")
    
    print("\n5. Check README.md for detailed documentation")
    
    print("\n" + "=" * 80)
    print("  For support, refer to README.md or contact your system administrator")
    print("=" * 80 + "\n")


def main():
    """Main setup routine."""
    print("\n" + "=" * 80)
    print(" " * 20 + "📒 LEDGER SYSTEM SETUP")
    print(" " * 25 + "Version 1.0.0")
    print("=" * 80)
    
    try:
        check_python_version()
        create_venv()
        
        print("\n⚠️  Please activate the virtual environment and re-run this script:")
        
        if sys.platform == "win32":
            print("   venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        
        print("   python setup.py\n")
        
        # Check if we're in a venv
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            print("✅ Running in virtual environment")
            install_dependencies()
            create_env_file()
            initialize_database()
            create_sample_accounts()
            show_next_steps()
        else:
            print("⚠️  Not running in virtual environment yet")
        
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
