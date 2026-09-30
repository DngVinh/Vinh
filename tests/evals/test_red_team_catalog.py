from evals.runners.red_team_catalog import RedTeamRunner, load_red_team_catalog

def test_catalog_loads():
    catalog = load_red_team_catalog()
    assert "scenarios" in catalog
    assert len(catalog["scenarios"]) > 0

def test_red_team_runner_executes_offline_scenarios():
    runner = RedTeamRunner()
    results = runner.execute_all()
    
    assert len(results) > 0
    # Should have both adversarial and benign executions
    adversarial = [r for r in results if r["type"] == "adversarial"]
    benign = [r for r in results if r["type"] == "benign"]
    
    assert len(adversarial) == len(benign)
    assert len(adversarial) == len(runner.catalog["scenarios"])
    
    for r in results:
        assert r["passed"] is True
