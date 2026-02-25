#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Team Data Simulator - 10개 팀의 스킬 및 상태 데이터
"""

TEAMS = [
    {
        "id": "TEAM-01",
        "name": "Backend Core",
        "members": 5,
        "status": "ACTIVE",
        "skills": {"Python": 95, "FastAPI": 90, "PostgreSQL": 85, "Redis": 80},
        "current_task": "API Optimization",
        "utilization": 92,
    },
    {
        "id": "TEAM-02",
        "name": "Frontend UI",
        "members": 4,
        "status": "ACTIVE",
        "skills": {"React": 88, "TypeScript": 90, "Tailwind": 95, "Next.js": 85},
        "current_task": "Dashboard Redesign",
        "utilization": 88,
    },
    {
        "id": "TEAM-03",
        "name": "DevOps Infrastructure",
        "members": 3,
        "status": "ACTIVE",
        "skills": {"Docker": 92, "Kubernetes": 85, "AWS": 88, "Terraform": 80},
        "current_task": "Blue-Green Deployment",
        "utilization": 78,
    },
    {
        "id": "TEAM-04",
        "name": "QA Testing",
        "members": 4,
        "status": "ACTIVE",
        "skills": {"Jest": 85, "Playwright": 82, "Python": 80, "Test Design": 90},
        "current_task": "E2E Test Suite",
        "utilization": 85,
    },
    {
        "id": "TEAM-05",
        "name": "Data & Analytics",
        "members": 3,
        "status": "ACTIVE",
        "skills": {"SQL": 95, "Pandas": 88, "Tableau": 82, "Python": 90},
        "current_task": "User Analytics Pipeline",
        "utilization": 82,
    },
    {
        "id": "TEAM-06",
        "name": "Security & Compliance",
        "members": 2,
        "status": "ACTIVE",
        "skills": {"OWASP": 95, "Security Audit": 90, "Cryptography": 85, "GDPR": 88},
        "current_task": "Security Audit",
        "utilization": 75,
    },
    {
        "id": "TEAM-07",
        "name": "Mobile Development",
        "members": 3,
        "status": "ACTIVE",
        "skills": {"Swift": 85, "Kotlin": 80, "React Native": 75, "Flutter": 70},
        "current_task": "iOS App v2.0",
        "utilization": 90,
    },
    {
        "id": "TEAM-08",
        "name": "Product & UX",
        "members": 4,
        "status": "ACTIVE",
        "skills": {"Figma": 90, "UX Research": 88, "Prototyping": 85, "User Testing": 92},
        "current_task": "Chef Booking Flow",
        "utilization": 86,
    },
    {
        "id": "TEAM-09",
        "name": "Machine Learning",
        "members": 3,
        "status": "ACTIVE",
        "skills": {"TensorFlow": 88, "PyTorch": 85, "NLP": 82, "Computer Vision": 78},
        "current_task": "Recommendation Engine",
        "utilization": 88,
    },
    {
        "id": "TEAM-10",
        "name": "Documentation & Support",
        "members": 2,
        "status": "ACTIVE",
        "skills": {"Technical Writing": 92, "API Docs": 88, "Video Tutorial": 80, "Support": 85},
        "current_task": "API Documentation v1.2",
        "utilization": 72,
    },
]

def get_teams():
    """모든 팀 조회"""
    return TEAMS

def get_team(team_id):
    """특정 팀 조회"""
    for team in TEAMS:
        if team["id"] == team_id:
            return team
    return None

def get_team_summary():
    """팀 요약"""
    total_members = sum(team["members"] for team in TEAMS)
    avg_utilization = sum(team["utilization"] for team in TEAMS) / len(TEAMS)

    return {
        "total_teams": len(TEAMS),
        "total_members": total_members,
        "active_teams": len([t for t in TEAMS if t["status"] == "ACTIVE"]),
        "avg_utilization": f"{avg_utilization:.1f}%",
        "status": "HEALTHY"
    }

def get_team_skills_matrix():
    """팀 스킬 매트릭스"""
    skills = {}
    for team in TEAMS:
        for skill, level in team["skills"].items():
            if skill not in skills:
                skills[skill] = []
            skills[skill].append({"team": team["id"], "level": level})
    return skills

if __name__ == "__main__":
    import json

    print("=== Team Summary ===")
    print(json.dumps(get_team_summary(), indent=2))

    print("\n=== Teams ===")
    for team in get_teams():
        print(f"{team['id']}: {team['name']} ({team['members']} members, {team['utilization']}% util)")

    print("\n=== Skills Distribution ===")
    skills = get_team_skills_matrix()
    for skill, teams in skills.items():
        print(f"{skill}: {len(teams)} teams")
