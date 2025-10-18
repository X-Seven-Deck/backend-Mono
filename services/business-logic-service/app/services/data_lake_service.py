"""
Enterprise Data Lake Service

Manages data ingestion, cataloging, and governance for the data lake.
Implements automatic classification, encryption, and metadata management.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class DataClassification(Enum):
    """Data classification levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class DataAsset:
    """Represents a data asset in the data lake"""
    
    def __init__(
        self,
        asset_id: str,
        path: str,
        schema: Dict,
        metadata: Dict,
        classification: DataClassification,
        tags: List[str],
        created_at: datetime,
        tenant_id: str
    ):
        self.asset_id = asset_id
        self.path = path
        self.schema = schema
        self.metadata = metadata
        self.classification = classification
        self.tags = tags
        self.created_at = created_at
        self.tenant_id = tenant_id
    
    def to_dict(self) -> Dict:
        return {
            "asset_id": self.asset_id,
            "path": self.path,
            "schema": self.schema,
            "metadata": self.metadata,
            "classification": self.classification.value,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "tenant_id": self.tenant_id
        }


class DataGovernance:
    """Data governance and compliance engine"""
    
    PII_FIELDS = [
        'email', 'phone', 'ssn', 'credit_card', 'address',
        'first_name', 'last_name', 'date_of_birth', 'passport'
    ]
    
    PHI_FIELDS = [
        'medical_record', 'diagnosis', 'prescription', 'treatment',
        'health_insurance', 'patient_id'
    ]
    
    async def classify_data(self, data: Any) -> DataClassification:
        """Classify data based on content"""
        try:
            if isinstance(data, dict):
                # Check for PII/PHI fields
                if self._contains_pii(data):
                    return DataClassification.RESTRICTED
                elif self._contains_sensitive_business_data(data):
                    return DataClassification.CONFIDENTIAL
                elif self._contains_internal_data(data):
                    return DataClassification.INTERNAL
            
            return DataClassification.PUBLIC
            
        except Exception as e:
            logger.error(f"Error classifying data: {e}")
            # Default to most restrictive
            return DataClassification.RESTRICTED
    
    def _contains_pii(self, data: Dict) -> bool:
        """Check if data contains PII"""
        keys = set(str(k).lower() for k in self._get_all_keys(data))
        return any(pii_field in keys for pii_field in self.PII_FIELDS)
    
    def _contains_sensitive_business_data(self, data: Dict) -> bool:
        """Check for sensitive business data"""
        sensitive_keywords = ['revenue', 'profit', 'salary', 'cost', 'pricing', 'strategy']
        keys = set(str(k).lower() for k in self._get_all_keys(data))
        return any(keyword in keys for keyword in sensitive_keywords)
    
    def _contains_internal_data(self, data: Dict) -> bool:
        """Check for internal-only data"""
        internal_keywords = ['internal', 'employee', 'staff', 'operation']
        keys = set(str(k).lower() for k in self._get_all_keys(data))
        return any(keyword in keys for keyword in internal_keywords)
    
    def _get_all_keys(self, data: Dict, prefix: str = '') -> List[str]:
        """Recursively get all keys from nested dict"""
        keys = []
        for k, v in data.items():
            full_key = f"{prefix}.{k}" if prefix else k
            keys.append(full_key)
            if isinstance(v, dict):
                keys.extend(self._get_all_keys(v, full_key))
        return keys
    
    async def encrypt_pii(self, data: Any) -> Any:
        """Encrypt PII fields in data"""
        # TODO: Integrate with HashiCorp Vault for encryption
        # For now, return data as-is (placeholder)
        logger.info("PII encryption applied (placeholder)")
        return data


class DataCatalog:
    """Data catalog for asset discovery and metadata management"""
    
    def __init__(self):
        self.catalog: Dict[str, DataAsset] = {}
    
    async def register_asset(
        self,
        path: str,
        schema: Dict,
        metadata: Dict,
        classification: DataClassification,
        tags: List[str]
    ) -> str:
        """Register a new data asset in the catalog"""
        asset_id = self._generate_asset_id(path, metadata)
        
        asset = DataAsset(
            asset_id=asset_id,
            path=path,
            schema=schema,
            metadata=metadata,
            classification=classification,
            tags=tags,
            created_at=datetime.utcnow(),
            tenant_id=metadata.get('tenant_id', 'unknown')
        )
        
        self.catalog[asset_id] = asset
        logger.info(f"Registered asset {asset_id} in catalog")
        
        return asset_id
    
    async def get_asset(self, asset_id: str) -> Optional[DataAsset]:
        """Retrieve asset from catalog"""
        return self.catalog.get(asset_id)
    
    async def search_assets(
        self,
        tenant_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        classification: Optional[DataClassification] = None
    ) -> List[DataAsset]:
        """Search for assets by criteria"""
        results = list(self.catalog.values())
        
        if tenant_id:
            results = [a for a in results if a.tenant_id == tenant_id]
        
        if tags:
            results = [a for a in results if any(tag in a.tags for tag in tags)]
        
        if classification:
            results = [a for a in results if a.classification == classification]
        
        return results
    
    def _generate_asset_id(self, path: str, metadata: Dict) -> str:
        """Generate unique asset ID"""
        content = f"{path}:{json.dumps(metadata, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class S3Storage:
    """S3-compatible storage interface"""
    
    def __init__(self):
        self.storage_path = "/data/lake"  # Local path for development
    
    async def store(
        self,
        data: Any,
        partition_by: List[str],
        format: str = 'parquet'
    ) -> str:
        """Store data in data lake with partitioning"""
        # Generate path based on partitions
        path_parts = []
        for partition_key in partition_by:
            if isinstance(data, dict) and partition_key in data:
                path_parts.append(f"{partition_key}={data[partition_key]}")
            elif partition_key == 'date':
                path_parts.append(f"date={datetime.utcnow().strftime('%Y-%m-%d')}")
        
        path = f"{self.storage_path}/{'/'.join(path_parts)}/data.{format}"
        
        # TODO: Implement actual S3 storage
        logger.info(f"Stored data at {path} (placeholder)")
        
        return path


class EnterpriseDataLake:
    """
    Enterprise Data Lake Manager
    
    Provides centralized data ingestion, cataloging, and governance
    for all business data across tenants.
    """
    
    def __init__(self):
        self.storage = S3Storage()
        self.catalog = DataCatalog()
        self.governance = DataGovernance()
    
    async def ingest_data(
        self,
        source: str,
        data: Any,
        metadata: Dict
    ) -> DataAsset:
        """
        Ingest data with automatic cataloging and governance
        
        Args:
            source: Data source identifier
            data: The data to ingest
            metadata: Metadata about the data
        
        Returns:
            DataAsset: The registered data asset
        """
        try:
            # Classify data
            classification = await self.governance.classify_data(data)
            logger.info(f"Data classified as {classification.value}")
            
            # Apply encryption based on classification
            if classification in [DataClassification.RESTRICTED, DataClassification.CONFIDENTIAL]:
                data = await self.governance.encrypt_pii(data)
            
            # Store in data lake
            asset_path = await self.storage.store(
                data=data,
                partition_by=['tenant_id', 'date', 'source'],
                format='parquet'
            )
            
            # Infer schema
            schema = self._infer_schema(data)
            
            # Generate tags
            tags = self._generate_tags(data, metadata, source)
            
            # Register in catalog
            asset_id = await self.catalog.register_asset(
                path=asset_path,
                schema=schema,
                metadata={
                    **metadata,
                    'source': source,
                    'ingestion_time': datetime.utcnow().isoformat()
                },
                classification=classification,
                tags=tags
            )
            
            asset = await self.catalog.get_asset(asset_id)
            logger.info(f"Successfully ingested data: {asset_id}")
            
            return asset
            
        except Exception as e:
            logger.error(f"Error ingesting data: {e}", exc_info=True)
            raise
    
    async def query_catalog(
        self,
        tenant_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        classification: Optional[DataClassification] = None
    ) -> List[DataAsset]:
        """Query the data catalog"""
        return await self.catalog.search_assets(
            tenant_id=tenant_id,
            tags=tags,
            classification=classification
        )
    
    def _infer_schema(self, data: Any) -> Dict:
        """Infer schema from data"""
        if isinstance(data, dict):
            schema = {}
            for key, value in data.items():
                schema[key] = type(value).__name__
            return schema
        elif isinstance(data, list) and len(data) > 0:
            return self._infer_schema(data[0])
        else:
            return {"type": type(data).__name__}
    
    def _generate_tags(self, data: Any, metadata: Dict, source: str) -> List[str]:
        """Generate tags for data asset"""
        tags = [source]
        
        # Add tenant tag
        if 'tenant_id' in metadata:
            tags.append(f"tenant:{metadata['tenant_id']}")
        
        # Add template tag
        if 'template_type' in metadata:
            tags.append(f"template:{metadata['template_type']}")
        
        # Add data type tags
        if isinstance(data, dict):
            if 'order' in str(data).lower():
                tags.append('orders')
            if 'customer' in str(data).lower():
                tags.append('customers')
            if 'inventory' in str(data).lower():
                tags.append('inventory')
        
        return tags


# Singleton instance
_data_lake_instance: Optional[EnterpriseDataLake] = None


def get_data_lake_service() -> EnterpriseDataLake:
    """Get or create data lake service instance"""
    global _data_lake_instance
    if _data_lake_instance is None:
        _data_lake_instance = EnterpriseDataLake()
    return _data_lake_instance
