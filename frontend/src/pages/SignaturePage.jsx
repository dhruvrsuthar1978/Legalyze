import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { PenTool, Check, X, FileText, Download, Shield, AlertCircle } from 'lucide-react';
import { useDispatch } from 'react-redux';
import { showToast } from '../store/uiSlice';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';

function SignaturePage() {
  const { id } = useParams();
  const dispatch = useDispatch();
  
  const [signatureModal, setSignatureModal] = useState(false);
  const [signatureName, setSignatureName] = useState('');
  const [signatureText, setSignatureText] = useState('');
  const [signatureError, setSignatureError] = useState('');
  const [document, setDocument] = useState({
    id: id || '1',
    name: 'Employment Agreement.pdf',
    uploadedAt: '2025-01-15',
    parties: [
      { name: 'ABC Corp', role: 'Employer', signed: true, signedAt: '2025-01-15 10:30 AM', status: 'verified' },
      { name: 'John Doe', role: 'Employee', signed: false, signedAt: null, status: 'pending' },
    ],
  });

  const currentUser = 'Employee'; // In real app, get from auth state
  const currentParty = document.parties.find(p => p.role === currentUser);
  const allSigned = document.parties.every(p => p.signed);

  const handleOpenSignature = () => {
    setSignatureModal(true);
    setSignatureName('');
    setSignatureText('');
    setSignatureError('');
  };

  const handleSignDocument = () => {
    // Validate signature
    if (!signatureName.trim()) {
      setSignatureError('Please enter your full name');
      return;
    }

    if (signatureName.trim().length < 2) {
      setSignatureError('Name must be at least 2 characters');
      return;
    }

    // Simulate signing process
    setTimeout(() => {
      const updatedParties = document.parties.map(p => 
        p.role === currentUser 
          ? { ...p, signed: true, signedAt: new Date().toLocaleString(), status: 'signed', signatureText: signatureName.trim() }
          : p
      );

      setDocument({ ...document, parties: updatedParties });
      setSignatureModal(false);

      dispatch(showToast({
        type: 'success',
        title: 'Document Signed Successfully',
        message: 'Your signature has been recorded and the document is being verified.',
      }));

      // Simulate verification after 2 seconds
      setTimeout(() => {
        const verifiedParties = document.parties.map(p => 
          p.role === currentUser 
            ? { ...p, status: 'verified' }
            : p
        );
        setDocument({ ...document, parties: verifiedParties });

        dispatch(showToast({
          type: 'success',
          title: 'Signature Verified',
          message: 'Your signature has been verified successfully.',
        }));
      }, 2000);
    }, 500);
  };

  const getStatusBadge = (status) => {
    const badges = {
      pending: { variant: 'warning', label: 'Pending' },
      signed: { variant: 'info', label: 'Signed' },
      verified: { variant: 'success', label: 'Verified' },
      invalid: { variant: 'error', label: 'Invalid' },
    };
    return badges[status] || badges.pending;
  };

  const getStatusIcon = (status) => {
    const icons = {
      pending: AlertCircle,
      signed: PenTool,
      verified: Shield,
      invalid: X,
    };
    return icons[status] || AlertCircle;
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Digital Signature</h1>
          <p className="text-gray-600 mt-1">Sign contracts digitally within the application</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" className="gap-2">
            <Download className="w-4 h-4" style={{ color: '#4b5563' }} />
            Download
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Document Preview */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <FileText className="w-5 h-5 text-blue-600" />
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">{document.name}</h2>
                  <p className="text-sm text-gray-600">Uploaded {document.uploadedAt}</p>
                </div>
              </div>
              {allSigned && (
                <Badge variant="success" className="gap-1">
                  <Shield className="w-3 h-3" />
                  All Parties Signed
                </Badge>
              )}
            </div>

            {/* Document Content */}
            <div className="bg-white border-2 border-gray-200 rounded-lg p-8 max-h-[600px] overflow-y-auto shadow-inner">
              <div className="space-y-6 text-sm leading-relaxed">
                <div className="text-center border-b pb-4">
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">EMPLOYMENT AGREEMENT</h2>
                  <p className="text-sm text-gray-600">Contract ID: {document.id}</p>
                </div>

                <div className="space-y-4">
                  <p className="font-semibold">PARTIES:</p>
                  <p>This Employment Agreement (&quot;Agreement&quot;) is entered into on January 15, 2025, between:</p>
                  <ul className="list-disc list-inside space-y-1 ml-4">
                    <li><strong>ABC Corp</strong> (&quot;Employer&quot;)</li>
                    <li><strong>John Doe</strong> (&quot;Employee&quot;)</li>
                  </ul>

                  <p className="font-semibold mt-6">1. POSITION AND DUTIES</p>
                  <p>The Employee is hired as a Software Engineer and will perform duties including but not limited to software development, code review, and technical documentation as reasonably assigned by the Employer.</p>

                  <p className="font-semibold mt-6">2. COMPENSATION</p>
                  <p>The Employee will receive an annual salary of $85,000, paid bi-weekly. Salary reviews will be conducted annually.</p>

                  <p className="font-semibold mt-6">3. BENEFITS</p>
                  <p>The Employee will be entitled to standard benefits including health insurance, dental coverage, 401(k) matching up to 5%, and 15 days of paid time off annually.</p>

                  <p className="font-semibold mt-6">4. TERMINATION</p>
                  <p>Either party may terminate this agreement with 30 days written notice. The Employer may terminate immediately for cause.</p>

                  <p className="font-semibold mt-6">5. CONFIDENTIALITY</p>
                  <p>The Employee agrees to maintain confidentiality of all proprietary information and trade secrets of the Employer.</p>
                </div>

                {/* Signature Section */}
                <div className="mt-12 pt-8 border-t-2 border-gray-300">
                  <p className="font-semibold mb-6">SIGNATURES:</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {document.parties.map((party, index) => (
                      <div key={index} className="space-y-2">
                        <p className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
                          {party.role} Signature
                        </p>
                        <div className={`border-b-2 pb-3 h-16 flex items-end ${
                          party.signed ? 'border-blue-600' : 'border-gray-300'
                        }`}>
                          {party.signed && (
                            <p className="text-3xl text-blue-600 font-signature">
                              {party.signatureText || party.name}
                            </p>
                          )}
                        </div>
                        <div className="flex items-center justify-between">
                          <p className="text-xs text-gray-600">
                            {party.signed ? `Signed: ${party.signedAt}` : 'Pending signature'}
                          </p>
                          {party.signed && (
                            <Badge variant={getStatusBadge(party.status).variant} className="text-xs">
                              {getStatusBadge(party.status).label}
                            </Badge>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Signature Status */}
          <Card>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Signature Status</h3>
            <div className="space-y-4">
              {document.parties.map((party, index) => {
                const StatusIcon = getStatusIcon(party.status);
                const statusBadge = getStatusBadge(party.status);
                
                return (
                  <div key={index} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                    <StatusIcon className={`w-5 h-5 mt-0.5 ${
                      party.status === 'verified' ? 'text-green-600' :
                      party.status === 'signed' ? 'text-blue-600' :
                      party.status === 'invalid' ? 'text-red-600' :
                      'text-yellow-600'
                    }`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className="text-sm font-medium text-gray-900">{party.name}</p>
                          <p className="text-xs text-gray-600">{party.role}</p>
                        </div>
                        <Badge variant={statusBadge.variant} className="shrink-0">
                          {statusBadge.label}
                        </Badge>
                      </div>
                      {party.signed && (
                        <p className="text-xs text-gray-500 mt-1">
                          {party.signedAt}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* Action Card */}
          {!currentParty?.signed ? (
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Ready to Sign?</h3>
              <div className="space-y-4">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <p className="text-sm text-blue-900 font-medium mb-1">Review Before Signing</p>
                  <p className="text-xs text-blue-700">
                    Please read the entire document carefully before signing.
                  </p>
                </div>
                <p className="text-sm text-gray-600">
                  By clicking &quot;Sign Document&quot;, you electronically sign this agreement and agree to all terms and conditions.
                </p>
                <Button onClick={handleOpenSignature} className="w-full gap-2">
                  <PenTool className="w-4 h-4" style={{ color: 'white' }} />
                  Sign Document
                </Button>
              </div>
            </Card>
          ) : (
            <Card className="bg-green-50 border-green-200">
              <div className="flex items-start gap-3">
                <Check className="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-lg font-semibold text-green-900 mb-2">
                    {currentParty.status === 'verified' ? 'Signature Verified!' : 'Document Signed!'}
                  </h3>
                  <p className="text-sm text-green-800 mb-3">
                    {currentParty.status === 'verified' 
                      ? 'Your signature has been verified. A copy has been sent to your email.'
                      : 'Your signature is being verified. This may take a few moments.'}
                  </p>
                  {currentParty.status === 'verified' && (
                    <div className="flex items-center gap-2 mt-3 pt-3 border-t border-green-200">
                      <Shield className="w-4 h-4 text-green-700" />
                      <p className="text-xs text-green-700 font-medium">
                        Verification ID: {Math.random().toString(36).substr(2, 9).toUpperCase()}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </Card>
          )}

          {/* Info Card */}
          <Card className="bg-gray-50">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">About Digital Signatures</h3>
            <div className="space-y-2 text-xs text-gray-600">
              <p>• Application-level signature for internal records</p>
              <p>• Not a government-certified digital signature</p>
              <p>• Signature data stored via backend API</p>
              <p>• Time-stamped and logged for audit trail</p>
            </div>
          </Card>
        </div>
      </div>

      {/* Signature Modal */}
      <Modal
        isOpen={signatureModal}
        onClose={() => setSignatureModal(false)}
        title="Sign Document"
        size="md"
        footer={
          <>
            <Button variant="outline" onClick={() => setSignatureModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleSignDocument} className="gap-2">
              <PenTool className="w-4 h-4" style={{ color: 'white' }} />
              Confirm Signature
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex gap-3">
              <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-yellow-900 mb-1">Important Notice</p>
                <p className="text-xs text-yellow-800">
                  By signing this document, you agree to all terms and conditions. This action cannot be undone.
                </p>
              </div>
            </div>
          </div>

          <Input
            label="Full Legal Name"
            placeholder="Enter your full name as it appears on official documents"
            value={signatureName}
            onChange={(e) => {
              setSignatureName(e.target.value);
              setSignatureError('');
            }}
            error={signatureError}
            helperText="Your name will be used as your electronic signature"
            autoFocus
          />

          {signatureName.trim() && (
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <p className="text-xs text-gray-600 mb-2">Signature Preview:</p>
              <div className="border-b-2 border-blue-600 pb-2">
                <p className="text-3xl text-blue-600 font-signature">{signatureName}</p>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Date: {new Date().toLocaleString()}
              </p>
            </div>
          )}

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-xs text-blue-900">
              <strong>Legal Disclaimer:</strong> This is an application-level electronic signature. 
              It is recorded for internal purposes and does not constitute a legally certified digital signature.
            </p>
          </div>
        </div>
      </Modal>
    </div>
  );
}

export default SignaturePage;