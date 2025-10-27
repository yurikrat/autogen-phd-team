#!/usr/bin/env python3
"""Teste simples para verificar funcionamento básico do AutoGen."""

import asyncio
import os
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient


async def main():
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERRO: OPENAI_API_KEY não encontrada")
        return
    
    print("✅ API Key encontrada")
    
    # Criar modelo
    model_client = OpenAIChatCompletionClient(
        model="gpt-4.1-mini",
        api_key=api_key,
    )
    
    print("✅ Modelo criado")
    
    # Criar agentes simples
    agent1 = AssistantAgent(
        name="Agent1",
        model_client=model_client,
        system_message="Você é um assistente útil. Responda de forma breve e objetiva.",
    )
    
    agent2 = AssistantAgent(
        name="Agent2",
        model_client=model_client,
        system_message="Você é um assistente que valida respostas. Diga 'APROVADO' se a resposta anterior foi boa.",
    )
    
    print("✅ Agentes criados")
    
    # Criar team
    team = RoundRobinGroupChat(
        participants=[agent1, agent2],
        termination_condition=MaxMessageTermination(5),
    )
    
    print("✅ Team criado")
    print("\n" + "="*80)
    print("INICIANDO EXECUÇÃO")
    print("="*80 + "\n")
    
    # Executar
    task = "Diga olá e explique em uma frase o que você faz."
    
    try:
        await Console(team.run_stream(task=task))
        print("\n" + "="*80)
        print("EXECUÇÃO CONCLUÍDA")
        print("="*80)
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

