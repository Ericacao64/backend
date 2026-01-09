from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class AssetMetadata:
    id: str
    fileName: str
    fileType: str
    uploadDate: str
    fileSize: int
    blobUrl: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)



