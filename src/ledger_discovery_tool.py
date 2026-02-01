#!/usr/bin/env python3
"""
Ledger / Accounting Engine - Discovery Tool
============================================
Sistema de descoberta de domínio contábil e regulatório.

Este sistema força o entendimento completo do contexto legal,
regulatório e contábil ANTES de gerar qualquer código.

Uso:
    python ledger_discovery_tool.py
    
Funcionalidades:
- Descoberta de contexto legal e regulatório
- Definição de modelo contábil
- Configuração de dupla entrada
- Estratégias de correção e auditoria
- Geração automática do sistema completo

Version: 1.0.0
Author: Financial Systems Architecture
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class LedgerDiscoveryTool:
    """Interactive discovery tool for Ledger/Accounting Engine design."""
    
    def __init__(self):
        self.config = {}
        self.current_phase = 1
        self.total_phases = 8
        
    def clear_screen(self):
        """Clear terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_header(self, title: str):
        """Display section header."""
        print("\n" + "=" * 80)
        print(f" {title}")
        print("=" * 80 + "\n")
    
    def show_banner(self):
        """Display welcome banner."""
        self.clear_screen()
        print("=" * 80)
        print(" " * 15 + "📒 LEDGER / ACCOUNTING ENGINE")
        print(" " * 20 + "Discovery & Design Tool")
        print(" " * 25 + "v1.0.0")
        print("=" * 80)
        print("\n🎯 REGRAS FUNDAMENTAIS:\n")
        print("   1. NÃO GERE CÓDIGO IMEDIATAMENTE")
        print("   2. NÃO ASSUMA REGRAS CONTÁBEIS")
        print("   3. TUDO DEVE SER AUDITÁVEL")
        print("   4. NADA É APAGADO OU ATUALIZADO")
        print("   5. ERROS SÃO CORRIGIDOS, NÃO REMOVIDOS")
        print("   6. SEMPRE SEPARAR FATO, REGRA E VISÃO")
        print("\n" + "=" * 80)
        input("\nPressione Enter para iniciar o processo de descoberta...")
    
    def get_choice(self, prompt: str, options: List[str], allow_multiple: bool = False) -> Any:
        """Get user choice from options."""
        print(f"\n{prompt}\n")
        for i, option in enumerate(options, 1):
            print(f"   [{i}] {option}")
        
        if allow_multiple:
            print("\n   (Digite os números separados por vírgula para múltipla escolha)")
        
        while True:
            choice = input("\nSua escolha: ").strip()
            
            if allow_multiple:
                try:
                    choices = [int(c.strip()) for c in choice.split(',')]
                    if all(1 <= c <= len(options) for c in choices):
                        return [options[c-1] for c in choices]
                    print("❌ Escolha inválida. Tente novamente.")
                except ValueError:
                    print("❌ Formato inválido. Use números separados por vírgula.")
            else:
                try:
                    idx = int(choice)
                    if 1 <= idx <= len(options):
                        return options[idx - 1]
                    print("❌ Escolha inválida. Tente novamente.")
                except ValueError:
                    print("❌ Digite um número válido.")
    
    def get_text_input(self, prompt: str, required: bool = True) -> str:
        """Get text input from user."""
        while True:
            value = input(f"\n{prompt}: ").strip()
            if value or not required:
                return value
            print("❌ Este campo é obrigatório.")
    
    def get_yes_no(self, prompt: str) -> bool:
        """Get yes/no answer."""
        while True:
            answer = input(f"\n{prompt} (sim/não): ").strip().lower()
            if answer in ['sim', 's', 'yes', 'y']:
                return True
            elif answer in ['não', 'nao', 'n', 'no']:
                return False
            print("❌ Responda 'sim' ou 'não'.")
    
    # ========================
    # PHASE 1: Legal Context
    # ========================
    
    def phase1_legal_context(self):
        """Phase 1: Legal and Business Context."""
        self.clear_screen()
        self.show_header(f"FASE {self.current_phase}/{self.total_phases} - CONTEXTO LEGAL E DE NEGÓCIO")
        
        print("Antes de qualquer decisão técnica, preciso entender o CONTEXTO LEGAL.\n")
        
        # 1.1 Sector
        sector_options = [
            "Bancário / Instituição Financeira",
            "Pagamentos / Fintech",
            "Mercado de Capitais / Trading",
            "Petróleo e Gás",
            "Energia / Utilities",
            "Telecomunicações",
            "Governo / Setor Público",
            "Outro (especificar)"
        ]
        
        sector = self.get_choice("1.1. Em que SETOR este ledger será utilizado?", sector_options)
        
        if sector == "Outro (especificar)":
            sector = self.get_text_input("Especifique o setor")
        
        self.config['sector'] = sector
        
        # 1.2 Legal Value
        legal_value_options = [
            "Sim, base para reporte oficial",
            "Sim, base para auditoria",
            "Sim, base para faturamento",
            "Não, apenas uso interno",
            "Não sei"
        ]
        
        legal_value = self.get_choice(
            "1.2. Este ledger possui VALOR LEGAL ou REGULATÓRIO?",
            legal_value_options,
            allow_multiple=True
        )
        
        self.config['legal_value'] = legal_value
        
        # 1.3 Regulations
        has_regulations = self.get_yes_no("1.3. Existem normas aplicáveis? (IFRS, GAAP, regulador bancário, etc.)")
        
        if has_regulations:
            regulations = self.get_text_input("Especifique as normas aplicáveis")
            self.config['regulations'] = regulations
        else:
            self.config['regulations'] = "Não aplicável"
        
        # 1.4 Responsibility
        responsibility_options = [
            "Contabilidade",
            "Financeiro",
            "Compliance",
            "Área técnica",
            "Regulador externo",
            "Outro"
        ]
        
        responsibility = self.get_choice(
            "1.4. Quem é RESPONSÁVEL pelos números produzidos?",
            responsibility_options
        )
        
        if responsibility == "Outro":
            responsibility = self.get_text_input("Especifique o responsável")
        
        self.config['responsibility'] = responsibility
        
        self.show_phase_summary("FASE 1 - CONTEXTO LEGAL", {
            "Setor": self.config['sector'],
            "Valor Legal/Regulatório": ', '.join(self.config['legal_value']) if isinstance(self.config['legal_value'], list) else self.config['legal_value'],
            "Normas Aplicáveis": self.config['regulations'],
            "Responsável": self.config['responsibility']
        })
        
        input("\nPressione Enter para continuar para a próxima fase...")
        self.current_phase += 1
    
    # ========================
    # PHASE 2: Accounting Model
    # ========================
    
    def phase2_accounting_model(self):
        """Phase 2: Economic Facts and Events."""
        self.clear_screen()
        self.show_header(f"FASE {self.current_phase}/{self.total_phases} - MODELO CONTÁBIL (NÚCLEO DO SISTEMA)")
        
        print("Ledger não registra dados. Registra FATOS.\n")
        
        # 2.1 Economic Facts
        print("2.1. Quais FATOS ECONÔMICOS este sistema deve registrar?")
        print("     (Exemplos: pagamento, consumo, produção, venda, ajuste, provisão)\n")
        
        facts = []
        for i in range(1, 6):
            fact = self.get_text_input(f"Fato {i}", required=(i <= 3))
            if fact:
                facts.append(fact)
            else:
                break
        
        self.config['economic_facts'] = facts
        
        # 2.2 Fact Types
        fact_type_options = [
            "Financeiros (dinheiro)",
            "Físicos com valor financeiro (energia, barril, volume)",
            "Ambos"
        ]
        
        fact_types = self.get_choice("2.2. Esses fatos são:", fact_type_options)
        self.config['fact_types'] = fact_types
        
        # 2.3 Occurrence
        occurrence_options = [
            "Em tempo real",
            "Em lote",
            "Após fechamento operacional",
            "Múltiplas formas"
        ]
        
        occurrence = self.get_choice("2.3. Esses fatos ocorrem:", occurrence_options)
        self.config['fact_occurrence'] = occurrence
        
        # 2.4 Error Possibility
        can_have_errors = self.get_yes_no("2.4. Um fato pode ser registrado ERRADO?")
        self.config['can_have_errors'] = can_have_errors
        
        if can_have_errors:
            error_explanation = self.get_text_input("Explique brevemente os casos de erro")
            self.config['error_cases'] = error_explanation
        
        self.show_phase_summary("FASE 2 - MODELO CONTÁBIL", {
            "Fatos Econômicos": ', '.join(self.config['economic_facts']),
            "Tipos de Fatos": self.config['fact_types'],
            "Ocorrência": self.config['fact_occurrence'],
            "Pode ter erros": "Sim" if self.config['can_have_errors'] else "Não"
        })
        
        input("\nPressione Enter para continuar...")
        self.current_phase += 1
    
    # ========================
    # PHASE 3: Double Entry
    # ========================
    
    def phase3_double_entry(self):
        """Phase 3: Double Entry and Ledger Structure."""
        self.clear_screen()
        self.show_header(f"FASE {self.current_phase}/{self.total_phases} - DUPLA ENTRADA E ESTRUTURA DO LEDGER")
        
        print("Agora o coração do sistema.\n")
        
        # 3.1 Double Entry
        double_entry_options = [
            "Sim (obrigatório)",
            "Sim (simplificada)",
            "Não"
        ]
        
        double_entry = self.get_choice("3.1. O ledger seguirá DUPLA ENTRADA?", double_entry_options)
        self.config['double_entry'] = double_entry
        
        if double_entry == "Não":
            explanation = self.get_text_input("Explique por quê não usará dupla entrada")
            self.config['no_double_entry_reason'] = explanation
        
        # 3.2 Account Types
        print("\n3.2. Quais TIPOS DE CONTA existirão?")
        print("     (Exemplos: ativo, passivo, receita, despesa)\n")
        
        account_types = []
        for i in range(1, 8):
            account_type = self.get_text_input(f"Tipo de Conta {i}", required=(i <= 3))
            if account_type:
                account_types.append(account_type)
            else:
                break
        
        self.config['account_types'] = account_types
        
        # 3.3 Chart of Accounts
        has_coa = self.get_choice(
            "3.3. Existe PLANO DE CONTAS definido?",
            ["Sim", "Não", "Parcial"]
        )
        self.config['has_chart_of_accounts'] = has_coa
        
        # 3.4 COA Mutability
        coa_mutability_options = [
            "Pode mudar com o tempo",
            "É fixo e versionado"
        ]
        
        coa_mutability = self.get_choice("3.4. O plano de contas:", coa_mutability_options)
        self.config['coa_mutability'] = coa_mutability
        
        self.show_phase_summary("FASE 3 - DUPLA ENTRADA", {
            "Dupla Entrada": self.config['double_entry'],
            "Tipos de Conta": ', '.join(self.config['account_types']),
            "Plano de Contas": self.config['has_chart_of_accounts'],
            "Mutabilidade": self.config['coa_mutability']
        })
        
        input("\nPressione Enter para continuar...")
        self.current_phase += 1
    
    # ========================
    # PHASE 4: Corrections
    # ========================
    
    def phase4_corrections(self):
        """Phase 4: Immutability, Corrections and History."""
        self.clear_screen()
        self.show_header(f"FASE {self.current_phase}/{self.total_phases} - IMUTABILIDADE, CORREÇÕES E HISTÓRICO")
        
        print("Ledger NÃO APAGA.\n")
        
        # 4.1 Correction Method
        correction_options = [
            "Lançamento de estorno",
            "Lançamento compensatório",
            "Ambos",
            "Ainda não definido"
        ]
        
        correction_method = self.get_choice(
            "4.1. Como erros devem ser corrigidos?",
            correction_options,
            allow_multiple=True
        )
        self.config['correction_method'] = correction_method
        
        # 4.2 Approval Required
        approval_options = [
            "Sim, sempre",
            "Não",
            "Depende do valor",
            "Depende do tipo de correção"
        ]
        
        approval = self.get_choice("4.2. Correções exigem APROVAÇÃO?", approval_options)
        self.config['correction_approval'] = approval
        
        if "Depende" in approval:
            approval_rules = self.get_text_input("Explique as regras de aprovação")
            self.config['approval_rules'] = approval_rules
        
        # 4.3 History Retention
        history_options = [
            "Sim, indefinidamente",
            "Sim, por período específico",
            "Não"
        ]
        
        history = self.get_choice("4.3. É necessário manter HISTÓRICO COMPLETO?", history_options)
        self.config['history_retention'] = history
        
        if "período específico" in history:
            retention_period = self.get_text_input("Especifique o período de retenção (ex: 7 anos)")
            self.config['retention_period'] = retention_period
        
        # Exceptions
        has_exceptions = self.get_yes_no("Existem exceções às regras de correção?")
        if has_exceptions:
            exceptions = self.get_text_input("Explique as exceções")
            self.config['correction_exceptions'] = exceptions
        
        self.show_phase_summary("FASE 4 - CORREÇÕES E HISTÓRICO", {
            "Método de Correção": ', '.join(self.config['correction_method']) if isinstance(self.config['correction_method'], list) else self.config['correction_method'],
            "Aprovação": self.config['correction_approval'],
            "Retenção de Histórico": self.config['history_retention']
        })
        
        input("\nPressione Enter para continuar...")
        self.current_phase += 1
    
    # ========================
    # PHASE 5: Views & Reports
    # ========================
    
    def phase5_views_reports(self):
        """Phase 5: Closings, Views and Reports."""
        self.clear_screen()
        self.show_header(f"FASE {self.current_phase}/{self.total_phases} - VISÕES, FECHAMENTO E RELATÓRIOS")
        
        print("Ledger gera MÚLTIPLAS VISÕES.\n")
        
        # 5.1 Closings
        closing_options = [
            "Diário",
            "Mensal",
            "Trimestral",
            "Anual",
            "Não aplicável"
        ]
        
        closings = self.get_choice(
            "5.1. Existem FECHAMENTOS contábeis?",
            closing_options,
            allow_multiple=True
        )
        self.config['closings'] = closings
        
        # 5.2 Post-Closing Behavior
        if "Não aplicável" not in closings:
            post_closing_options = [
                "Lançamentos são bloqueados",
                "Só lançamentos de ajuste",
                "Nada muda"
            ]
            
            post_closing = self.get_choice("5.2. Após o fechamento:", post_closing_options)
            self.config['post_closing_behavior'] = post_closing
        
        # 5.3 Required Views
        view_options = [
            "Visão contábil",
            "Visão gerencial",
            "Visão regulatória",
            "Visão por contrato/ativo",
            "Visão fiscal",
            "Outra"
        ]
        
        views = self.get_choice(
            "5.3. Quais VISÕES são necessárias?",
            view_options,
            allow_multiple=True
        )
        self.config['required_views'] = views
        
        # 5.4 Report Requirements
        report_requirements_options = [
            "Reproduzíveis",
            "Auditáveis",
            "Assináveis",
            "Exportáveis"
        ]
        
        report_reqs = self.get_choice(
            "5.4. Relatórios precisam ser:",
            report_requirements_options,
            allow_multiple=True
        )
        self.config['report_requirements'] = report_reqs
        
        self.show_phase_summary("FASE 5 - VISÕES E RELATÓRIOS", {
            "Fechamentos": ', '.join(self.config['closings']) if isinstance(self.config['closings'], list) else self.config['closings'],
            "Visões Necessárias": ', '.join(self.config['required_views']),
            "Requisitos de Relatórios": ', '.join(self.config['report_requirements'])
        })
        
        input("\nPressione Enter para continuar...")
        self.current_phase += 1
    
    # ========================
    # PHASE 6: Integrations
    # ========================
    
    def phase6_integrations(self):
        """Phase 6: Integrations and Relations with Other Systems."""
        self.clear_screen()
        self.show_header(f"FASE {self.current_phase}/{self.total_phases} - INTEGRAÇÕES E RELAÇÃO COM OUTROS SISTEMAS")
        
        # 6.1 Event Sources
        source_options = [
            "Core bancário",
            "Sistema operacional",
            "Medidores/sensores",
            "Sistemas legados",
            "Manual",
            "API externa",
            "Arquivo em lote"
        ]
        
        event_sources = self.get_choice(
            "6.1. De onde vêm os eventos?",
            source_options,
            allow_multiple=True
        )
        self.config['event_sources'] = event_sources
        
        # 6.2 Output Destinations
        destination_options = [
            "ERP",
            "Regulador",
            "BI",
            "Auditoria",
            "Data Lake",
            "Outro sistema financeiro"
        ]
        
        destinations = self.get_choice(
            "6.2. Ledger envia dados para:",
            destination_options,
            allow_multiple=True
        )
        self.config['output_destinations'] = destinations
        
        # 6.3 Source of Truth
        source_of_truth_options = [
            "Sim, sempre",
            "Não",
            "Apenas para alguns números"
        ]
        
        source_of_truth = self.get_choice(
            "6.3. Ledger é a FONTE FINAL DA VERDADE?",
            source_of_truth_options
        )
        self.config['is_source_of_truth'] = source_of_truth
        
        if "alguns números" in source_of_truth:
            which_numbers = self.get_text_input("Para quais números o ledger é fonte da verdade?")
            self.config['source_of_truth_scope'] = which_numbers
        
        self.show_phase_summary("FASE 6 - INTEGRAÇÕES", {
            "Fontes de Eventos": ', '.join(self.config['event_sources']),
            "Destinos de Dados": ', '.join(self.config['output_destinations']),
            "Fonte da Verdade": self.config['is_source_of_truth']
        })
        
        input("\nPressione Enter para continuar...")
        self.current_phase += 1
    
    # ========================
    # PHASE 7: Non-Functional
    # ========================
    
    def phase7_nonfunctional(self):
        """Phase 7: Audit, Security and Performance."""
        self.clear_screen()
        self.show_header(f"FASE {self.current_phase}/{self.total_phases} - REQUISITOS NÃO FUNCIONAIS")
        
        # 7.1 Entry Requirements
        entry_requirements_options = [
            "Origem",
            "Autor",
            "Timestamp",
            "Assinatura lógica",
            "Hash",
            "IP de origem",
            "Sistema de origem"
        ]
        
        entry_reqs = self.get_choice(
            "7.1. Cada lançamento precisa de:",
            entry_requirements_options,
            allow_multiple=True
        )
        self.config['entry_requirements'] = entry_reqs
        
        # 7.2 Volume
        volume_options = [
            "< 1M lançamentos/dia",
            "1–10M lançamentos/dia",
            "10-100M lançamentos/dia",
            "> 100M lançamentos/dia"
        ]
        
        volume = self.get_choice("7.2. Volume esperado:", volume_options)
        self.config['expected_volume'] = volume
        
        # 7.3 Latency
        latency_options = [
            "Imediata (< 1s)",
            "Segundos (1-10s)",
            "Minutos",
            "Horas (processamento em lote)"
        ]
        
        latency = self.get_choice("7.3. Latência aceitável:", latency_options)
        self.config['acceptable_latency'] = latency
        
        # 7.4 Backup and DR
        needs_dr = self.get_yes_no("7.4. Sistema necessita de Disaster Recovery?")
        self.config['needs_dr'] = needs_dr
        
        if needs_dr:
            rto = self.get_text_input("RTO (Recovery Time Objective) esperado")
            rpo = self.get_text_input("RPO (Recovery Point Objective) esperado")
            self.config['rto'] = rto
            self.config['rpo'] = rpo
        
        self.show_phase_summary("FASE 7 - REQUISITOS NÃO FUNCIONAIS", {
            "Requisitos por Lançamento": ', '.join(self.config['entry_requirements']),
            "Volume Esperado": self.config['expected_volume'],
            "Latência Aceitável": self.config['acceptable_latency'],
            "Disaster Recovery": "Sim" if self.config['needs_dr'] else "Não"
        })
        
        input("\nPressione Enter para validação final...")
        self.current_phase += 1
    
    # ========================
    # PHASE 8: Validation
    # ========================
    
    def phase8_validation(self):
        """Phase 8: Final Validation."""
        self.clear_screen()
        self.show_header(f"FASE {self.current_phase}/{self.total_phases} - VALIDAÇÃO FINAL")
        
        print("Vou resumir o entendimento do LEDGER.\n")
        
        summary = {
            "Setor": self.config.get('sector', 'N/A'),
            "Valor legal/regulatório": ', '.join(self.config.get('legal_value', [])) if isinstance(self.config.get('legal_value'), list) else self.config.get('legal_value', 'N/A'),
            "Normas aplicáveis": self.config.get('regulations', 'N/A'),
            "Responsável": self.config.get('responsibility', 'N/A'),
            "Fatos econômicos": ', '.join(self.config.get('economic_facts', [])),
            "Tipos de fatos": self.config.get('fact_types', 'N/A'),
            "Modelo de dupla entrada": self.config.get('double_entry', 'N/A'),
            "Tipos de conta": ', '.join(self.config.get('account_types', [])),
            "Plano de contas": self.config.get('has_chart_of_accounts', 'N/A'),
            "Estratégia de correção": ', '.join(self.config.get('correction_method', [])) if isinstance(self.config.get('correction_method'), list) else self.config.get('correction_method', 'N/A'),
            "Fechamentos": ', '.join(self.config.get('closings', [])) if isinstance(self.config.get('closings'), list) else self.config.get('closings', 'N/A'),
            "Visões exigidas": ', '.join(self.config.get('required_views', [])),
            "Fontes de eventos": ', '.join(self.config.get('event_sources', [])),
            "Destinos de dados": ', '.join(self.config.get('output_destinations', [])),
            "Fonte da verdade": self.config.get('is_source_of_truth', 'N/A'),
            "Requisitos de auditoria": ', '.join(self.config.get('entry_requirements', [])),
            "Volume esperado": self.config.get('expected_volume', 'N/A'),
            "Latência aceitável": self.config.get('acceptable_latency', 'N/A')
        }
        
        print("=" * 80)
        print("RESUMO DO SISTEMA DE LEDGER")
        print("=" * 80)
        print()
        
        for key, value in summary.items():
            print(f"• {key:.<40} {value}")
        
        print("\n" + "=" * 80)
        
        is_correct = self.get_yes_no("\nEste resumo está CORRETO?")
        
        if not is_correct:
            corrections = self.get_text_input("O que precisa ser corrigido?", required=False)
            self.config['corrections_needed'] = corrections
            print("\n⚠️  Por favor, reinicie o processo com as correções necessárias.")
            return False
        
        self.config['validated'] = True
        self.config['validation_timestamp'] = datetime.now().isoformat()
        
        return True
    
    # ========================
    # Helper Methods
    # ========================
    
    def show_phase_summary(self, title: str, data: Dict[str, str]):
        """Show phase summary."""
        print("\n" + "-" * 80)
        print(f"✅ {title} - CONCLUÍDO")
        print("-" * 80)
        for key, value in data.items():
            print(f"   {key}: {value}")
        print("-" * 80)
    
    def save_configuration(self) -> str:
        """Save configuration to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ledger_config_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        
        return filename
    
    def generate_system(self):
        """Generate complete ledger system based on configuration."""
        self.clear_screen()
        self.show_header("🔨 GERAÇÃO DO SISTEMA")
        
        print("O sistema será gerado com os seguintes componentes:\n")
        print("   ✓ Motor de ledger imutável")
        print("   ✓ Modelo de dupla entrada")
        print("   ✓ Controle de eventos contábeis")
        print("   ✓ Mecanismo de correção por estorno")
        print("   ✓ Trilhas de auditoria")
        print("   ✓ Relatórios reproduzíveis")
        print("   ✓ Documentação para auditor")
        print("   ✓ Testes automatizados")
        print("   ✓ Scripts de deployment")
        
        print("\n" + "=" * 80)
        confirm = self.get_yes_no("Confirmar geração do sistema?")
        
        if not confirm:
            print("\n❌ Geração cancelada.")
            return
        
        # Save configuration
        config_file = self.save_configuration()
        print(f"\n✅ Configuração salva em: {config_file}")
        
        print("\n🚀 Iniciando geração do sistema...")
        print("\nO sistema completo será criado em um momento...")
        
        return config_file
    
    def run(self):
        """Run the discovery process."""
        self.show_banner()
        
        try:
            # Execute all phases
            self.phase1_legal_context()
            self.phase2_accounting_model()
            self.phase3_double_entry()
            self.phase4_corrections()
            self.phase5_views_reports()
            self.phase6_integrations()
            self.phase7_nonfunctional()
            
            # Final validation
            if self.phase8_validation():
                config_file = self.generate_system()
                
                if config_file:
                    print("\n" + "=" * 80)
                    print("✅ PROCESSO DE DESCOBERTA CONCLUÍDO COM SUCESSO!")
                    print("=" * 80)
                    print(f"\nConfiguração salva em: {config_file}")
                    print("\nPróximos passos:")
                    print("   1. Revisar o arquivo de configuração")
                    print("   2. Executar o gerador de código")
                    print("   3. Configurar o banco de dados")
                    print("   4. Realizar testes")
                    print("\n" + "=" * 80)
        
        except KeyboardInterrupt:
            print("\n\n❌ Processo interrompido pelo usuário.")
            sys.exit(0)
        except Exception as e:
            print(f"\n\n❌ Erro durante o processo: {e}")
            sys.exit(1)


def main():
    """Main entry point."""
    tool = LedgerDiscoveryTool()
    tool.run()


if __name__ == "__main__":
    main()
