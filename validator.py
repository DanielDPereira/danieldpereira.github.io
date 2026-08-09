"""
validator.py - Validador do arquivo portfolio-data.json.

Verifica a integridade, tipos e presença de campos obrigatórios no JSON do portfólio,
retornando mensagens claras e descritivas para quaisquer inconsistências encontradas.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Garante suporte a UTF-8 na saída do console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def validate_portfolio_data(data: Dict[str, Any]) -> List[str]:
    """
    Valida a estrutura dos dados do portfólio.
    Retorna uma lista de strings contendo mensagens de erro.
    Retorna lista vazia caso todos os dados estejam válidos.
    """
    errors: List[str] = []

    if not isinstance(data, dict):
        return ["ERRO: O elemento raiz do arquivo JSON deve ser um objeto/dicionário."]

    # 1. Validação das chaves de primeiro nível
    required_sections = [
        "profile",
        "about",
        "education",
        "experiences",
        "skills",
        "projects",
        "certificates",
    ]
    for section in required_sections:
        if section not in data:
            errors.append(f"ERRO: Seção obrigatória '{section}' ausente no arquivo JSON.")

    if errors:
        return errors

    # 2. Validação da seção 'profile'
    profile = data.get("profile", {})
    if not isinstance(profile, dict):
        errors.append("ERRO: A seção 'profile' deve ser um dicionário/objeto.")
    else:
        required_profile_fields = [
            "name",
            "heroEyebrow",
            "heroTitle",
            "heroDescription",
            "contactMessage",
            "footerText",
        ]
        for field in required_profile_fields:
            val = profile.get(field)
            if not val or not isinstance(val, str) or not val.strip():
                errors.append(f"ERRO: profile.{field} é obrigatório e não pode estar vazio.")

        if "socials" in profile:
            if not isinstance(profile["socials"], list):
                errors.append("ERRO: profile.socials deve ser uma lista.")
            else:
                for idx, soc in enumerate(profile["socials"]):
                    if not isinstance(soc, dict):
                        errors.append(f"ERRO: profile.socials[{idx}] deve ser um objeto.")
                        continue
                    for f in ["label", "icon", "url"]:
                        if not soc.get(f):
                            errors.append(f"ERRO: profile.socials[{idx}].{f} está vazio.")

        if "cta" in profile:
            if not isinstance(profile["cta"], list):
                errors.append("ERRO: profile.cta deve ser uma lista.")
            else:
                for idx, item in enumerate(profile["cta"]):
                    if not isinstance(item, dict):
                        errors.append(f"ERRO: profile.cta[{idx}] deve ser um objeto.")
                        continue
                    for f in ["label", "url", "type"]:
                        if not item.get(f):
                            errors.append(f"ERRO: profile.cta[{idx}].{f} está vazio.")

        if "stats" in profile:
            if not isinstance(profile["stats"], list):
                errors.append("ERRO: profile.stats deve ser uma lista.")
            else:
                for idx, item in enumerate(profile["stats"]):
                    if not isinstance(item, dict):
                        errors.append(f"ERRO: profile.stats[{idx}] deve ser um objeto.")
                        continue
                    for f in ["value", "label"]:
                        if not item.get(f):
                            errors.append(f"ERRO: profile.stats[{idx}].{f} está vazio.")

    # 3. Validação da seção 'about'
    about = data.get("about", {})
    if not isinstance(about, dict):
        errors.append("ERRO: A seção 'about' deve ser um dicionário/objeto.")
    else:
        if not about.get("greeting") or not isinstance(about.get("greeting"), str):
            errors.append("ERRO: about.greeting é obrigatório.")
        if not isinstance(about.get("paragraphs"), list) or not about.get("paragraphs"):
            errors.append("ERRO: about.paragraphs deve ser uma lista não vazia de textos.")

    # 4. Validação da seção 'education'
    education = data.get("education", [])
    if not isinstance(education, list):
        errors.append("ERRO: A seção 'education' deve ser uma lista.")
    else:
        for idx, item in enumerate(education):
            if not isinstance(item, dict):
                errors.append(f"ERRO: education[{idx}] deve ser um objeto.")
                continue
            for f in ["degree", "institution", "period", "type", "description"]:
                if not item.get(f):
                    errors.append(f"ERRO: education[{idx}].{f} está vazio.")

    # 5. Validação da seção 'experiences'
    experiences = data.get("experiences", [])
    if not isinstance(experiences, list):
        errors.append("ERRO: A seção 'experiences' deve ser uma lista.")
    else:
        for idx, item in enumerate(experiences):
            if not isinstance(item, dict):
                errors.append(f"ERRO: experiences[{idx}] deve ser um objeto.")
                continue
            for f in ["title", "company", "period", "type", "location", "description"]:
                if not item.get(f):
                    errors.append(f"ERRO: experiences[{idx}].{f} está vazio.")

    # 6. Validação da seção 'skills'
    skills = data.get("skills", [])
    if not isinstance(skills, list):
        errors.append("ERRO: A seção 'skills' deve ser uma lista.")
    else:
        for idx, item in enumerate(skills):
            if not isinstance(item, dict):
                errors.append(f"ERRO: skills[{idx}] deve ser um objeto.")
                continue
            for f in ["name", "icon", "alt", "category"]:
                if not item.get(f):
                    errors.append(f"ERRO: skills[{idx}].{f} está vazio.")

    # 7. Validação da seção 'projects'
    projects = data.get("projects", [])
    if not isinstance(projects, list):
        errors.append("ERRO: A seção 'projects' deve ser uma lista.")
    else:
        for idx, item in enumerate(projects):
            if not isinstance(item, dict):
                errors.append(f"ERRO: projects[{idx}] deve ser um objeto.")
                continue
            for f in ["title", "description", "category", "year", "status", "thumbnail"]:
                if not item.get(f):
                    errors.append(f"ERRO: projects[{idx}].{f} está vazio.")
            if not isinstance(item.get("technologies"), list) or not item.get("technologies"):
                errors.append(f"ERRO: projects[{idx}].technologies deve ser uma lista não vazia.")

    # 8. Validação da seção 'certificates'
    certificates = data.get("certificates", [])
    if not isinstance(certificates, list):
        errors.append("ERRO: A seção 'certificates' deve ser uma lista.")
    else:
        for idx, item in enumerate(certificates):
            if not isinstance(item, dict):
                errors.append(f"ERRO: certificates[{idx}] deve ser um objeto.")
                continue
            for f in ["title", "url"]:
                if not item.get(f):
                    errors.append(f"ERRO: certificates[{idx}].{f} está vazio.")

    return errors


def validate_file(filepath: str = "portfolio-data.json") -> bool:
    """Carrega e valida o arquivo JSON especificado. Exibe mensagens no console."""
    path = Path(filepath)
    if not path.exists():
        print(f"ERRO: Arquivo '{filepath}' não foi encontrado.")
        return False

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERRO: Falha ao decodificar JSON do arquivo '{filepath}': {e}")
        return False

    errors = validate_portfolio_data(data)
    if errors:
        print(f"\n[ERRO] Validação de '{filepath}' falhou com {len(errors)} erro(s):")
        for err in errors:
            print(f"  - {err}")
        return False

    print(f"[OK] Arquivo '{filepath}' validado com sucesso! Nenhum erro encontrado.")
    return True


if __name__ == "__main__":
    file_to_check = sys.argv[1] if len(sys.argv) > 1 else "portfolio-data.json"
    success = validate_file(file_to_check)
    sys.exit(0 if success else 1)
