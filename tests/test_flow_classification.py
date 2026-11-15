"""Unit tests for flow classification, filtering rules, and Addendum 07 updates."""

from pathlib import Path
import pandas as pd
import pytest
from src.utils.paths import get_repo_root
from src.pipeline.flow_classification import FlowClassifier


@pytest.fixture(scope="module")
def classifier() -> FlowClassifier:
    rules_path = get_repo_root() / "features" / "flow_rules.yaml"
    assert rules_path.exists(), "flow_rules.yaml must exist."
    return FlowClassifier(rules_path=rules_path)


def test_preserved_rules(classifier: FlowClassifier):
    """Verifies that existing core rules for vendor, search, and website are preserved."""
    # Vendor (A)
    assert classifier.classify_flow_domain(pd.Series({"requested_server_name": "generativelanguage.googleapis.com"})) == "vendor"
    assert classifier.classify_flow_domain(pd.Series({"requested_server_name": "http-intake.logs.us5.datadoghq.com"})) == "vendor"
    assert classifier.classify_flow_domain(pd.Series({"requested_server_name": "agent.datadoghq.com"})) == "vendor"

    # Search (D)
    assert classifier.classify_flow_domain(pd.Series({"requested_server_name": "www.google.com"})) == "search"
    assert classifier.classify_flow_domain(pd.Series({"requested_server_name": "suggestqueries.google.com"})) == "search"

    # Website (Primary B6)
    assert classifier.classify_flow_domain(pd.Series({"requested_server_name": "meridian-tasks.vercel.app"})) == "website"
    assert classifier.classify_flow_domain(pd.Series({"requested_server_name": "en.wikipedia.org"})) == "website"
    assert classifier.classify_flow_domain(pd.Series({"requested_server_name": "upload.wikimedia.org"})) == "website"
    assert classifier.classify_flow_domain(pd.Series({"requested_server_name": "duckduckgo.com"})) == "website"


def test_classification_precedence(classifier: FlowClassifier):
    """Verifies strict match precedence: LAN -> vendor -> search -> os_background -> website -> unknown."""
    # Vendor takes precedence over googleapis.com background
    assert classifier.classify_flow_domain(pd.Series({"requested_server_name": "generativelanguage.googleapis.com"})) == "vendor"
    
    # Search takes precedence over google background
    assert classifier.classify_flow_domain(pd.Series({"requested_server_name": "www.google.com"})) == "search"

    # LAN takes precedence over everything
    row_lan = pd.Series({"requested_server_name": "android.local", "dst_port": 443})
    assert classifier.is_lan_traffic(row_lan) is True
    assert classifier.classify_flow_domain(row_lan) == "lan_excluded"


def test_personal_applications_background(classifier: FlowClassifier):
    """Verifies personal applications from Addendum 07 are classified as os_background."""
    personal_domains = [
        "spotify.com",
        "audio-ak.spotify.com",
        "spclient.wg.spotify.com",
        "dropbox.com",
        "api.dropbox.com",
        "zoom.us",
        "us04web.zoom.us",
        "skype.com",
        "api.skype.com",
        "mcafee.com",
        "download.mcafee.com",
    ]
    for domain in personal_domains:
        res = classifier.classify_flow_domain(pd.Series({"requested_server_name": domain}))
        assert res == "os_background", f"Domain {domain} should be os_background, got {res}"


def test_dry_run_domains_background(classifier: FlowClassifier):
    """Verifies dry-run only domains are classified as os_background."""
    dry_run_domains = [
        "grammarly.com",
        "extension.femetrics.grammarly.io",
        "honey.io",
        "brave.com",
        "youtube.com",
        "google.ae",
        "claude.ai",
        "anthropic.com",
        "api.anthropic.com",
    ]
    for domain in dry_run_domains:
        res = classifier.classify_flow_domain(pd.Series({"requested_server_name": domain}))
        assert res == "os_background", f"Domain {domain} should be os_background, got {res}"


def test_msn_edge_and_ad_trackers(classifier: FlowClassifier):
    """Verifies Edge/MSN news feed and tracker hosts are classified as os_background."""
    edge_news_domains = [
        "headtopics.com",
        "zigwheels.com",
        "carhp.in",
        "autocarpro.in",
        "bozokmedia.com",
        "theindustryoutlook.com",
        "scorecardresearch.com",
        "doubleclick.net",
        "servedbyadbutler.com",
        "googletagmanager.com",
        "google-analytics.com",
    ]
    for domain in edge_news_domains:
        res = classifier.classify_flow_domain(pd.Series({"requested_server_name": domain}))
        assert res == "os_background", f"Domain {domain} should be os_background, got {res}"


def test_infrastructure_and_oem_domains(classifier: FlowClassifier):
    """Verifies infrastructure, PKI, OEM, and updater domains are os_background."""
    infra_domains = [
        "lencr.org",
        "digicert.com",
        "sectigo.com",
        "usertrust.com",
        "pki.goog",
        "msftconnecttest.com",
        "msftncsi.com",
        "windowsupdate.com",
        "sfx.ms",
        "azureedge.net",
        "nvidia.com",
        "nvidiagrid.net",
        "geforce.com",
        "hp.com",
        "hpsmart.com",
        "hpgamestream.com",
        "falais.com",
        "pypi.org",
        "edgedl.me.gvt1.com",
        "update.googleapis.com",
    ]
    for domain in infra_domains:
        res = classifier.classify_flow_domain(pd.Series({"requested_server_name": domain}))
        assert res == "os_background", f"Domain {domain} should be os_background, got {res}"


def test_lan_traffic_exclusions(classifier: FlowClassifier):
    """Verifies that all LAN-only patterns and discovery protocols are flagged and excluded."""
    lan_cases = [
        pd.Series({"requested_server_name": "printer.local"}),
        pd.Series({"requested_server_name": "device._tcp.local"}),
        pd.Series({"requested_server_name": "service._udp.local"}),
        pd.Series({"requested_server_name": "Android.local"}),  # Phone on Wi-Fi (S0005-S0019)
        pd.Series({"requested_server_name": "wpad.domain.name"}),
        pd.Series({"requested_server_name": "_ldap._tcp.dc._msdcs.domain.name"}),
        pd.Series({"requested_server_name": "Cal"}),
        pd.Series({"dst_ip": "192.168.1.255"}),
        pd.Series({"dst_ip": "255.255.255.255"}),
        pd.Series({"dst_ip": "127.0.0.1"}),
        pd.Series({"dst_ip": "::1"}),
        pd.Series({"dst_port": 5353}),   # mDNS
        pd.Series({"dst_port": 1900}),   # SSDP
        pd.Series({"dst_port": 5355}),   # LLMNR
        pd.Series({"dst_port": 137}),    # NetBIOS Name
        pd.Series({"dst_port": 138}),    # NetBIOS Datagram
        pd.Series({"dst_port": 139}),    # NetBIOS Session
        pd.Series({"dst_port": 445}),    # SMB
        pd.Series({"dst_port": 67}),     # DHCP
        pd.Series({"dst_port": 123}),    # NTP
    ]
    for row in lan_cases:
        assert classifier.is_lan_traffic(row) is True, f"Failed to identify LAN traffic for row: {row.to_dict()}"
        assert classifier.classify_flow_domain(row) == "lan_excluded"

    # Test filter_lan_traffic DataFrame operation
    df_sample = pd.DataFrame([
        {"flow_id": "f1", "requested_server_name": "Android.local", "dst_port": 5353},
        {"flow_id": "f2", "requested_server_name": "meridian-tasks.vercel.app", "dst_port": 443},
    ])
    filtered_df = classifier.filter_lan_traffic(df_sample)
    assert len(filtered_df) == 1
    assert filtered_df.iloc[0]["flow_id"] == "f2"


def test_unresolved_domains_not_website(classifier: FlowClassifier):
    """Verifies unresolved domains (fastly-edge.com, cloudflare-ech.com) are NEVER classified as website."""
    unres_cases = [
        "fastly-edge.com",
        "dualstack.fastly-edge.com",
        "cloudflare-ech.com",
    ]
    for domain in unres_cases:
        cls = classifier.classify_flow_domain(pd.Series({"requested_server_name": domain}))
        assert cls == "unknown", f"Unresolved domain {domain} must be classified as 'unknown', got {cls}"
        assert cls != "website", f"Unresolved domain {domain} was erroneously classified as website!"
        assert cls != "os_background", f"Unresolved domain {domain} was prematurely classified as os_background!"
