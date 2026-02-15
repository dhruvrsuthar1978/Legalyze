import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { ChevronDown, Check, X } from 'lucide-react';
import { analysisService } from '../services/analysisService';
import { contractService } from '../services/contractService';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';

function ContractAnalysisPage() {
  const { id } = useParams();
  const [expandedClause, setExpandedClause] = useState(null);
  const [contract, setContract] = useState(null);
  const [clauses, setClauses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchContractData = async () => {
      try {
        setLoading(true);

        // Fetch contract metadata
        const contractData = await contractService.getContract(id);

        // Fetch analysis data (run analysis once if not available yet)
        let analysisData;
        try {
          analysisData = await analysisService.getClauseAnalysis(id);
        } catch (analysisError) {
          if (analysisError?.response?.status === 404) {
            analysisData = await analysisService.runAnalysis(id, 'sync');
          } else {
            throw analysisError;
          }
        }

        setContract({
          id,
          name: contractData.title || contractData.filename || 'Contract Analysis',
          uploadedAt: contractData.uploaded_at
            ? new Date(contractData.uploaded_at).toLocaleDateString()
            : 'Unknown',
          status: contractData.analysis_status || 'pending',
        });

        setClauses((analysisData.clauses || []).map(clause => ({
          id: clause.clause_id,
          title: clause.clause_type,
          risk: (clause.risk_level || 'Low').toLowerCase(),
          originalText: clause.original_text,
          plainEnglish: clause.simplified_text || 'Processing...',
          riskReason: clause.risk_reason || 'Analysis in progress...',
          suggestion: clause.suggestion || 'Generating suggestions...',
        })));

      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchContractData();
    }
  }, [id]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-8"></div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1">
              <div className="h-64 bg-gray-200 rounded"></div>
            </div>
            <div className="lg:col-span-2">
              <div className="h-96 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto space-y-6">
        <Card className="text-center p-12">
          <h2 className="text-xl font-semibold text-red-600 mb-2">Error Loading Contract</h2>
          <p className="text-gray-600">{error}</p>
          <Button className="mt-4" onClick={() => window.location.reload()}>
            Try Again
          </Button>
        </Card>
      </div>
    );
  }

  if (!contract) {
    return (
      <div className="max-w-7xl mx-auto space-y-6">
        <Card className="text-center p-12">
          <h2 className="text-xl font-semibold text-gray-600">Contract Not Found</h2>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{contract.name}</h1>
          <p className="text-gray-600 mt-1">Uploaded on {contract.uploadedAt}</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline">Download PDF</Button>
          <Button variant="outline">Download DOCX</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Clause List */}
        <div className="lg:col-span-1">
          <Card>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Clauses ({clauses.length})</h2>
            <div className="space-y-2">
              {clauses.map((clause) => (
                <button
                  key={clause.id}
                  onClick={() => setExpandedClause(clause.id === expandedClause ? null : clause.id)}
                  className={`w-full text-left p-3 rounded-lg border-2 transition-all ${
                    expandedClause === clause.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-gray-900 text-sm">{clause.title}</span>
                    <Badge variant={clause.risk}>
                      {clause.risk}
                    </Badge>
                  </div>
                </button>
              ))}
            </div>
          </Card>
        </div>

        {/* Details Panel */}
        <div className="lg:col-span-2">
          {expandedClause ? (
            <Card className="space-y-6">
              {clauses
                .filter(c => c.id === expandedClause)
                .map(clause => (
                  <div key={clause.id}>
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h2 className="text-2xl font-bold text-gray-900">{clause.title}</h2>
                        <Badge variant={clause.risk} className="mt-2">
                          {clause.risk} Risk
                        </Badge>
                      </div>
                    </div>

                    <div className="space-y-6">
                      {/* Original Text */}
                      <div className="p-4 bg-gray-50 rounded-lg">
                        <h3 className="text-sm font-semibold text-gray-700 mb-2 uppercase tracking-wide">
                          Original Legal Text
                        </h3>
                        <p className="text-gray-800 leading-relaxed">{clause.originalText}</p>
                      </div>

                      {/* Plain English */}
                      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <h3 className="text-sm font-semibold text-blue-900 mb-2 uppercase tracking-wide">
                          Plain English Explanation
                        </h3>
                        <p className="text-blue-800 leading-relaxed">{clause.plainEnglish}</p>
                      </div>

                      {/* Risk Reason */}
                      <div className={`p-4 rounded-lg border ${
                        clause.risk === 'high' ? 'bg-red-50 border-red-200' :
                        clause.risk === 'medium' ? 'bg-yellow-50 border-yellow-200' :
                        'bg-green-50 border-green-200'
                      }`}>
                        <h3 className={`text-sm font-semibold mb-2 uppercase tracking-wide ${
                          clause.risk === 'high' ? 'text-red-900' :
                          clause.risk === 'medium' ? 'text-yellow-900' :
                          'text-green-900'
                        }`}>
                          Risk Assessment
                        </h3>
                        <p className={`leading-relaxed ${
                          clause.risk === 'high' ? 'text-red-800' :
                          clause.risk === 'medium' ? 'text-yellow-800' :
                          'text-green-800'
                        }`}>
                          {clause.riskReason}
                        </p>
                      </div>

                      {/* AI Suggestion */}
                      <div className="p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
                        <h3 className="text-sm font-semibold text-indigo-900 mb-2 uppercase tracking-wide">
                          AI Suggestion
                        </h3>
                        <p className="text-indigo-800 leading-relaxed mb-4">{clause.suggestion}</p>
                        <div className="flex gap-2">
                          <Button size="sm" className="gap-2">
                            <Check className="w-4 h-4" style={{ color: 'white' }} />
                            Accept Suggestion
                          </Button>
                          <Button size="sm" variant="outline" className="gap-2">
                            <X className="w-4 h-4" style={{ color: '#4b5563' }} />
                            Reject
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
            </Card>
          ) : (
            <Card className="h-full flex items-center justify-center text-center p-12">
              <div>
                <ChevronDown className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  Select a Clause
                </h3>
                <p className="text-gray-600">
                  Click on any clause from the list to view its details and AI analysis
                </p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

export default ContractAnalysisPage;
