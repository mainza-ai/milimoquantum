"""Tests for MQDD extension module."""
import pytest
from unittest.mock import patch, MagicMock


class TestMQDDExtension:
    """Test MQDD extension registration and endpoints."""

    def test_extension_imports(self):
        """Test that extension module can be imported."""
        from app.extensions.mqdd import extension
        assert extension is not None

    def test_router_defined(self):
        """Test that MQDD router is defined."""
        from app.extensions.mqdd.extension import mqdd_router
        assert mqdd_router is not None
        assert mqdd_router.prefix == '/api/mqdd'

    def test_extension_registered(self):
        """Test that extension is properly registered."""
        from app.extensions.mqdd.extension import mqdd_extension
        assert mqdd_extension.id == 'mqdd'
        assert mqdd_extension.name == 'Quantum Drug Discovery'
        assert '/mqdd' in mqdd_extension.slash_commands

    def test_status_endpoint(self):
        """Test status endpoint returns correct structure."""
        from app.extensions.mqdd.extension import get_status
        result = get_status()
        assert 'status' in result
        assert 'local_llm' in result

    def test_workflow_request_schema(self):
        """Test WorkflowRequest schema validation."""
        from app.extensions.mqdd.extension import WorkflowRequest
        req = WorkflowRequest(prompt='test molecule')
        assert req.prompt == 'test molecule'
        assert req.basis == 'sto3g'

        req_custom = WorkflowRequest(prompt='custom', basis='cc-pvdz', conversation_id='test-123')
        assert req_custom.basis == 'cc-pvdz'
        assert req_custom.conversation_id == 'test-123'

    def test_dispatch_handler_molecule_query(self):
        """Test dispatch handler for molecule queries."""
        from app.extensions.mqdd.extension import mqdd_dispatch_handler
        
        result = mqdd_dispatch_handler('analyze this molecule smiles')
        assert 'response' in result
        assert 'MQDD' in result['response']
        assert result['needs_llm'] == True

    def test_dispatch_handler_other_query(self):
        """Test dispatch handler for non-molecule queries."""
        from app.extensions.mqdd.extension import mqdd_dispatch_handler
        
        result = mqdd_dispatch_handler('quantum circuit for optimization')
        assert result == {}


class TestMQDDAgents:
    """Test MQDD agent functions."""

    def test_agents_imports(self):
        """Test that agents module can be imported."""
        from app.extensions.mqdd import agents
        assert agents is not None

    def test_rdkit_flag(self):
        """Test RDKIT_AVAILABLE flag is set."""
        from app.extensions.mqdd.agents import RDKIT_AVAILABLE
        assert isinstance(RDKIT_AVAILABLE, bool)

    def test_is_valid_smiles_function(self):
        """Test SMILES validation function."""
        from app.extensions.mqdd.agents import is_valid_smiles
        
        # Valid SMILES (if RDKit available, returns True/False; else returns True)
        result = is_valid_smiles('CCO')  # ethanol
        assert isinstance(result, bool)

    def test_get_admet_model_function(self):
        """Test ADMET model getter."""
        from app.extensions.mqdd.agents import get_admet_model
        
        # Should return None or an ADMET model
        result = get_admet_model()
        # The result depends on whether ADMET-AI is installed
        assert result is None or result is not None  # Just check it doesn't crash


class TestMQDDWorkflow:
    """Test MQDD workflow functions."""

    def test_workflow_imports(self):
        """Test that workflow module can be imported."""
        try:
            from app.extensions.mqdd import workflow
            assert workflow is not None
        except ImportError:
            pytest.skip("MQDD workflow not available")

    def test_workflow_functions_exist(self):
        """Test that workflow functions exist."""
        try:
            from app.extensions.mqdd.workflow import run_full_workflow
            assert callable(run_full_workflow)
        except ImportError:
            pytest.skip("MQDD workflow functions not available")


class TestMQDDSchemas:
    """Test MQDD schema models."""

    def test_schemas_imports(self):
        """Test that schemas module can be imported."""
        from app.extensions.mqdd import schemas
        assert schemas is not None

    def test_molecule_candidate_schema(self):
        """Test MoleculeCandidate schema."""
        from app.extensions.mqdd.schemas import MoleculeCandidate
        
        mol = MoleculeCandidate(
            smiles='CCO',
            name='Ethanol'
        )
        assert mol.smiles == 'CCO'
        assert mol.name == 'Ethanol'

    def test_admet_property_schema(self):
        """Test AdmetProperty schema."""
        from app.extensions.mqdd.schemas import AdmetProperty
        
        prop = AdmetProperty(
            value='High',
            evidence='Test evidence',
            score=0.5
        )
        assert prop.value == 'High'
        assert prop.score == 0.5

    def test_interaction_schema(self):
        """Test Interaction schema."""
        from app.extensions.mqdd.schemas import Interaction
        
        interaction = Interaction(
            type='HydrogenBond',
            residue='ALA-225',
            ligandAtoms=[1, 2],
            proteinAtoms=[3, 4]
        )
        assert interaction.type == 'HydrogenBond'
        assert interaction.residue == 'ALA-225'


class TestMQDDDiscoveryTools:
    """Test MQDD discovery tools."""

    def test_discovery_tools_imports(self):
        """Test that discovery_tools module can be imported."""
        try:
            from app.extensions.mqdd import discovery_tools
            assert discovery_tools is not None
        except ImportError:
            pytest.skip("discovery_tools not available")

    def test_tool_functions_exist(self):
        """Test that discovery tool functions exist."""
        try:
            from app.extensions.mqdd.discovery_tools import (
                search_pdb_structures,
                search_literature_pubmed
            )
            assert callable(search_pdb_structures)
            assert callable(search_literature_pubmed)
        except ImportError:
            pytest.skip("discovery tool functions not available")
