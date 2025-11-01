import React, { useState, useEffect, useMemo, useCallback } from 'react';
import axios from 'axios';
import { Container, Row, Col, Table, Form, Button, Card, Alert, Modal, ProgressBar, Spinner, Dropdown, DropdownButton } from 'react-bootstrap';
import Fuse from 'fuse.js';
import { useDebounce } from 'use-debounce';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5050';

const normalizeStateKey = (state) => (state || '')
  .toLowerCase()
  .replace(/[^a-z0-9]/g, '');

const stateImageMap = new Map([
  ['maharashtra', 'Maharashtra.png'],
  ['tamilnadu', 'Tamil Nadu.png'],
  ['uttarpradesh', 'Uttar Pradesh.png'],
  ['karnataka', 'Karnataka.png'],
  ['kerala', 'Kerala.png'],
  ['gujarat', 'gujarat.png'],
  ['puducherry', 'Puduchery.png'],
  ['puduchery', 'Puduchery.png'],
  ['delhi', 'Delhi.png'],
  ['nationalcapitalterritoryofdelhi', 'Delhi.png'],
]);

// Component to render highlighted search results
const HighlightedText = ({ text, indices }) => {
  if (!text) return null;
  if (!indices || indices.length === 0) {
    return <span>{text}</span>;
  }

  const result = [];
  let lastIndex = 0;

  indices.forEach(([start, end], i) => {
    if (start > lastIndex) {
      result.push(<span key={`text-${i}-pre`}>{text.substring(lastIndex, start)}</span>);
    }
    result.push(<strong key={`match-${i}`}>{text.substring(start, end + 1)}</strong>);
    lastIndex = end + 1;
  });

  if (lastIndex < text.length) {
    result.push(<span key="text-post">{text.substring(lastIndex)}</span>);
  }

  return <span>{result}</span>;
};


// Circular progress component for validation and qualification
const CircularProgress = ({ value, max, size = 40, strokeWidth = 4, color = '#4CAF50' }) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const progress = max > 0 ? (value / max) * 100 : 0;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#e0e0e0"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={strokeDasharray}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>
      <div
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          fontSize: size * 0.3,
          fontWeight: 'bold',
          color: '#333',
          textAlign: 'center',
        }}
      >
        {value}/{max}
      </div>
    </div>
  );
};

function App() {
  const [centers, setCenters] = useState([]);
  const [file, setFile] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm] = useDebounce(searchTerm, 300);
  const [searchResults, setSearchResults] = useState([]);
  const [fuse, setFuse] = useState(null);
  const [selectedCities, setSelectedCities] = useState([]);
  const [selectedStates, setSelectedStates] = useState([]);
  const [allCities, setAllCities] = useState([]);
  const [allStates, setAllStates] = useState([]);
  const [validatedFilter, setValidatedFilter] = useState('all');
  const [qualifiedFilter, setQualifiedFilter] = useState('all');
  const [showStats, setShowStats] = useState(false);
  const [currentView, setCurrentView] = useState('cities');
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [editingCenterId, setEditingCenterId] = useState(null);
  const [editFormData, setEditFormData] = useState(null);
  const [noteDrafts, setNoteDrafts] = useState({});
  const [noteSaving, setNoteSaving] = useState({});
  const [selectedForDeletion, setSelectedForDeletion] = useState(new Set());
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [expandedStates, setExpandedStates] = useState(new Set());
  const [uploadProgress, setUploadProgress] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatusMessage, setUploadStatusMessage] = useState('');
  const [showDuplicateModal, setShowDuplicateModal] = useState(false);
  const [potentialDuplicates, setPotentialDuplicates] = useState([]);
  const [currentDuplicateIndex, setCurrentDuplicateIndex] = useState(0);
  const [isFindingDuplicates, setIsFindingDuplicates] = useState(false);
  const [isAutoMerging, setIsAutoMerging] = useState(false);

  const normalizeForSort = (value, fallback) => {
    if (value === null || value === undefined) return fallback;
    const trimmed = value.toString().trim();
    return trimmed === '' ? fallback : trimmed;
  };

  const sortByCityName = (a, b) => {
    const nameA = normalizeForSort(a, 'Unknown').toLowerCase();
    const nameB = normalizeForSort(b, 'Unknown').toLowerCase();
    return nameA.localeCompare(nameB);
  };

  const sortByStateName = (a, b) => {
    const nameA = normalizeForSort(a, 'Unknown State').toLowerCase();
    const nameB = normalizeForSort(b, 'Unknown State').toLowerCase();
    return nameA.localeCompare(nameB);
  };

  const formatCityLabel = (name) => normalizeForSort(name, 'Unknown');

  useEffect(() => {
    fetchCenters();
  }, []);

  const resolveState = useCallback((center) => {
    return center?.state?.trim() || 'Unknown State';
  }, []);

  const fetchCenters = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/centers`);
      const data = response.data;
      setCenters(data);
      
      const uniqueCities = [...new Set(data.map(center => center.city))].sort(sortByCityName);
      setAllCities(uniqueCities);

      const uniqueStates = [...new Set(data.map(center => resolveState(center)))].sort(sortByStateName);
      setAllStates(uniqueStates);

      const initialNotes = {};
      data.forEach(center => {
        initialNotes[center.id] = center.notes || '';
      });
      setNoteDrafts(initialNotes);
      setNoteSaving({});

      const fuseOptions = {
        keys: [
          { name: 'center_name', weight: 0.4 },
          { name: 'city', weight: 0.3 },
          { name: 'address', weight: 0.2 },
          { name: 'notes', weight: 0.1 }
        ],
        includeScore: true,
        includeMatches: true,
        threshold: 0.4,
        minMatchCharLength: 2,
      };
      setFuse(new Fuse(data, fuseOptions));

    } catch (error) {
      console.error('Error fetching centers:', error);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0] ?? null;
    setFile(selectedFile);
    setUploadProgress(null);
    setUploadStatusMessage('');
    setIsUploading(false);
  };

  const handleFileUpload = async () => {
    if (!file) {
      alert('Please select a file to upload.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setIsUploading(true);
    setUploadProgress(0);
    setUploadStatusMessage('Uploading...');

    try {
      await axios.post(`${API_BASE_URL}/api/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const { loaded, total } = progressEvent;
          if (typeof total === 'number' && total > 0) {
            const percent = Math.round((loaded * 100) / total);
            setUploadProgress(percent);
          }
        },
      });
      setUploadProgress(100);
      setUploadStatusMessage('Upload complete');
      alert('File uploaded successfully!');
      fetchCenters();
      setTimeout(() => {
        setUploadProgress(null);
        setUploadStatusMessage('');
      }, 3000);
    } catch (error) {
      console.error('Error uploading file:', error);
      const errorMessage = error.response?.data?.detail || 'Error uploading file.';
      alert(errorMessage);
      setUploadStatusMessage('Upload failed');
      setUploadProgress(null);
    }
    setIsUploading(false);
  };

  const handleRemoveDuplicates = async () => {
    if (window.confirm("Are you sure you want to remove duplicate records based on address? This cannot be undone.")) {
      try {
        const response = await axios.delete(`${API_BASE_URL}/api/deduplicate`);
        alert(`Removed ${response.data.duplicates_removed} duplicate records`);
        fetchCenters();
      } catch (error) {
        console.error('Error removing duplicates:', error);
        alert('Error removing duplicates');
      }
    }
  };

  const handleFindPotentialDuplicates = async () => {
    setIsFindingDuplicates(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/potential-duplicates`);
      if (response.data.length === 0) {
        alert("No potential duplicates found.");
      } else {
        setPotentialDuplicates(response.data);
        setCurrentDuplicateIndex(0);
        setShowDuplicateModal(true);
      }
    } catch (error) {
      console.error('Error finding potential duplicates:', error);
      alert('Error finding potential duplicates.');
    }
    setIsFindingDuplicates(false);
  };

  const handleAutoMergeDuplicates = async () => {
    if (window.confirm("Are you sure you want to automatically merge all similar duplicates? This action is irreversible and will merge records based on a similarity score > 85%, keeping the record with the lower ID in each pair.")) {
      setIsAutoMerging(true);
      try {
        const response = await axios.post(`${API_BASE_URL}/api/auto-merge-duplicates`);
        alert(`Auto-merge complete. Merged ${response.data.duplicates_merged} records.`);
        fetchCenters();
      } catch (error) {
        console.error('Error auto-merging duplicates:', error);
        alert('An error occurred during the auto-merge process.');
      }
      setIsAutoMerging(false);
    }
  };

  const handleMergeDuplicates = async (idToKeep, idToDelete) => {
    try {
      await axios.post(`${API_BASE_URL}/api/merge-duplicates`, {
        id_to_keep: idToKeep,
        id_to_delete: idToDelete,
      });

      const updatedDuplicates = potentialDuplicates.filter(
        (pair, index) =>
          index > currentDuplicateIndex &&
          pair.center1.id !== idToDelete &&
          pair.center2.id !== idToDelete
      );

      setPotentialDuplicates(updatedDuplicates);
      setCurrentDuplicateIndex(0);

      if (updatedDuplicates.length === 0) {
        setShowDuplicateModal(false);
        alert("All potential duplicates have been reviewed.");
      }

      fetchCenters();
    } catch (error) {
      console.error('Error merging duplicates:', error);
      alert('Error merging duplicates.');
    }
  };

  const handleIgnoreDuplicate = () => {
    if (currentDuplicateIndex < potentialDuplicates.length - 1) {
      setCurrentDuplicateIndex(currentDuplicateIndex + 1);
    } else {
      setShowDuplicateModal(false);
      alert("All potential duplicates have been reviewed.");
    }
  };

  const handleSearchChange = (e) => setSearchTerm(e.target.value);
  const handleValidatedFilterChange = (e) => setValidatedFilter(e.target.value);
  const handleQualifiedFilterChange = (e) => setQualifiedFilter(e.target.value);

  const handleStateChange = (state) => {
    const newSelectedStates = selectedStates.includes(state)
      ? selectedStates.filter(s => s !== state)
      : [...selectedStates, state];
    setSelectedStates(newSelectedStates);
    const citiesInSelectedStates = [...new Set(centers.filter(c => newSelectedStates.includes(resolveState(c))).map(c => c.city))];
    setSelectedCities(selectedCities.filter(c => citiesInSelectedStates.includes(c)));
  };

  const handleCityChange = (city) => {
    setSelectedCities(prev => 
      prev.includes(city) ? prev.filter(c => c !== city) : [...prev, city]
    );
  };

  const handleEditClick = (center) => {
    setEditingCenterId(center.id);
    setEditFormData({
      center_name: center.center_name || '',
      address: center.address || '',
      contact_details: center.contact_details || '',
      google_maps_link: center.google_maps_link || '',
      city: center.city || '',
      validated: center.validated,
      qualified: center.qualified,
      notes: noteDrafts[center.id] ?? center.notes ?? '',
    });
  };

  const handleEditFieldChange = (field, value) => {
    setEditFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleCancelEdit = () => {
    setEditingCenterId(null);
    setEditFormData(null);
  };

  const handleSaveEdit = async () => {
    if (!editingCenterId || !editFormData) return;
    try {
      await axios.put(`${API_BASE_URL}/api/centers/${editingCenterId}`, { ...editFormData });
      alert('Center updated successfully');
      setEditingCenterId(null);
      setEditFormData(null);
      fetchCenters();
    } catch (error) {
      console.error('Error updating center:', error);
      alert('Error updating center');
    }
  };

  const handleNoteChange = (centerId, value) => {
    setNoteDrafts((prev) => ({ ...prev, [centerId]: value }));
  };

  const handleSaveNote = async (center) => {
    const noteContent = noteDrafts[center.id] ?? '';
    try {
      setNoteSaving((prev) => ({ ...prev, [center.id]: true }));
      const response = await axios.patch(`${API_BASE_URL}/api/centers/${center.id}/notes`, { notes: noteContent });
      const updatedCenter = response.data;
      setCenters((prev) => prev.map((item) => (item.id === center.id ? updatedCenter : item)));
      setNoteDrafts((prev) => ({ ...prev, [center.id]: updatedCenter.notes || '' }));
    } catch (error) {
      console.error('Error updating notes:', error);
      alert('Error updating notes');
    } finally {
      setNoteSaving((prev) => ({ ...prev, [center.id]: false }));
    }
  };

  const handleValidationToggle = async (centerId, validated) => {
    try {
      await axios.put(`${API_BASE_URL}/api/centers/${centerId}/validate`, {}, { params: { validated } });
      fetchCenters();
    } catch (error) {
      console.error('Error updating validation status:', error);
      alert('Error updating validation status');
    }
  };

  const handleQualificationToggle = async (centerId, qualified) => {
    try {
      await axios.put(`${API_BASE_URL}/api/centers/${centerId}/qualify`, {}, { params: { qualified } });
      fetchCenters();
    } catch (error) {
      console.error('Error updating qualification status:', error);
      alert('Error updating qualification status');
    }
  };

  const handleDeleteCenter = async (centerId, centerName) => {
    if (window.confirm(`Are you sure you want to delete the center "${centerName}"? This cannot be undone.`)) {
      try {
        await axios.delete(`${API_BASE_URL}/api/centers/${centerId}`);
        alert('Center deleted successfully');
        fetchCenters();
      } catch (error) {
        console.error('Error deleting center:', error);
        alert('Error deleting center');
      }
    }
  };

  const toggleCityValidation = async (city) => {
    try {
      const centersInCity = centers.filter(c => c.city === city);
      if (centersInCity.length === 0) {
        alert(`No centers found for city ${city}`);
        return;
      }
      const newValidatedStatus = !centersInCity[0].validated;
      await axios.put(`${API_BASE_URL}/api/cities/${encodeURIComponent(city)}/validate`, {}, { params: { validated: newValidatedStatus } });
      alert(`City ${city} validation status updated to ${newValidatedStatus ? 'Validated' : 'Not Validated'}`);
      fetchCenters();
    } catch (error) {
      console.error('Error updating city validation status:', error);
      alert('Error updating city validation status');
    }
  };

  const requestSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const sortedCenters = (data) => {
    const sortableData = [...data];
    if (sortConfig.key !== null) {
      sortableData.sort((a, b) => {
        let aValue = a[sortConfig.key];
        let bValue = b[sortConfig.key];
        if (typeof aValue === 'string') aValue = aValue.toLowerCase();
        if (typeof bValue === 'string') bValue = bValue.toLowerCase();
        if (sortConfig.direction === 'asc') {
          return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
        } else {
          return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
        }
      });
    }
    return sortableData;
  };

  const availableCities = useMemo(() => {
    if (selectedStates.length === 0) {
      return allCities;
    }
    return [...new Set(centers.filter(c => selectedStates.includes(resolveState(c))).map(c => c.city))].sort(sortByCityName);
  }, [selectedStates, allCities, centers, resolveState]);

  const processedCenters = useMemo(() => {
    let filtered = centers;

    if (debouncedSearchTerm && fuse) {
      const searchResults = fuse.search(debouncedSearchTerm);
      setSearchResults(searchResults);
      filtered = searchResults.map(result => result.item);
    } else {
      setSearchResults([]);
      filtered = centers;
    }

    filtered = filtered.filter(center => {
      const matchesState = selectedStates.length === 0 || selectedStates.includes(resolveState(center));
      const matchesCity = selectedCities.length === 0 || selectedCities.includes(center.city);
      const matchesValidated = validatedFilter === 'all' || (validatedFilter === 'validated' && center.validated) || (validatedFilter === 'unvalidated' && !center.validated);
      const matchesQualified = qualifiedFilter === 'all' || (qualifiedFilter === 'qualified' && center.qualified) || (qualifiedFilter === 'unqualified' && !center.qualified);
      return matchesState && matchesCity && matchesValidated && matchesQualified;
    });

    return filtered;
  }, [centers, debouncedSearchTerm, fuse, selectedStates, selectedCities, validatedFilter, qualifiedFilter, resolveState]);

  const cityCounts = processedCenters.reduce((acc, center) => {
    if (center.city) {
      acc[center.city] = (acc[center.city] || 0) + 1;
    }
    return acc;
  }, {});

  const stateCounts = useMemo(() => {
    const counts = {};
    processedCenters.forEach(center => {
      const state = resolveState(center);
      counts[state] = (counts[state] || 0) + 1;
    });
    return counts;
  }, [processedCenters, resolveState]);

  const contactStatus = processedCenters.reduce((acc, center) => {
    if (center.contact_details && center.contact_details.trim() !== '' && center.contact_details !== 'Not provided in text' && center.contact_details !== 'Information not available.' && center.contact_details !== 'No phone number available.') {
      acc.available = (acc.available || 0) + 1;
    } else {
      acc.unavailable = (acc.unavailable || 0) + 1;
    }
    return acc;
  }, { available: 0, unavailable: 0 });

  const centersWithLinks = processedCenters.filter(center => center.google_maps_link && center.google_maps_link.trim() !== '');

  const stats = {
    totalCenters: processedCenters.length,
    centersWithContact: contactStatus.available,
    centersWithoutContact: contactStatus.unavailable,
    centersWithMaps: centersWithLinks.length,
    citiesCount: Object.keys(cityCounts).length
  };

  const getStateImage = (state) => {
    if (!state) return '/images/states/unknown_state.svg';
    const key = normalizeStateKey(state);
    const mappedFile = stateImageMap.get(key);
    if (mappedFile) {
      return `/pictures/${encodeURIComponent(mappedFile)}`;
    }
    const fallbackName = state.trim().toLowerCase().replace(/\s+/g, '_');
    if (!fallbackName || fallbackName === 'unknown_state') {
      return '/images/states/unknown_state.svg';
    }
    return `/images/states/${fallbackName}.jpg`;
  };

  const handleCityClick = (city) => {
    setSelectedCities([city]);
    setCurrentView('centers');
  };

  const handleBackToCities = () => {
    setCurrentView('cities');
    setSelectedCities([]);
  };

  return (
    <Container fluid>
      <h1 className="my-4 text-center">
        {currentView === 'cities' ? 'CT Scan Centers Analytics Dashboard' : `CT Scan Centers in ${selectedCities.join(', ')}`}
      </h1>
      
      <Row className="mb-4">
        {currentView === 'centers' && (
          <Col md={12} className="mb-3">
            <Button variant="secondary" onClick={handleBackToCities}>&larr; Back to Cities</Button>
          </Col>
        )}
        <Col md={2} className="mb-3"><Card className="text-center bg-primary text-white h-100 shadow-sm"><Card.Body><Card.Title className="display-6">{stats.totalCenters}</Card.Title><Card.Text>Total Centers</Card.Text></Card.Body></Card></Col>
        <Col md={2} className="mb-3"><Card className="text-center bg-success text-white h-100 shadow-sm"><Card.Body><Card.Title className="display-6">{stats.centersWithContact}</Card.Title><Card.Text>With Contacts</Card.Text></Card.Body></Card></Col>
        <Col md={2} className="mb-3"><Card className="text-center bg-danger text-white h-100 shadow-sm"><Card.Body><Card.Title className="display-6">{stats.centersWithoutContact}</Card.Title><Card.Text>Without Contacts</Card.Text></Card.Body></Card></Col>
        <Col md={2} className="mb-3"><Card className="text-center bg-info text-white h-100 shadow-sm"><Card.Body><Card.Title className="display-6">{stats.centersWithMaps}</Card.Title><Card.Text>With Maps</Card.Text></Card.Body></Card></Col>
        <Col md={2} className="mb-3"><Card className="text-center bg-warning text-dark h-100 shadow-sm"><Card.Body><Card.Title className="display-6">{stats.citiesCount}</Card.Title><Card.Text>Locations</Card.Text></Card.Body></Card></Col>
        <Col md={2} className="mb-3"><Card className="text-center bg-secondary text-white h-100 shadow-sm"><Card.Body className="d-flex flex-column justify-content-center"><Button variant="light" onClick={() => setShowStats(!showStats)}>{showStats ? 'Hide' : 'Show'} Analytics</Button></Card.Body></Card></Col>
      </Row>

      <Row className="mb-4">
        <Col md={3}>
          <Form.Group><Form.Label>Search by name, city, or address:</Form.Label><Form.Control type="text" placeholder="Enter search term" value={searchTerm} onChange={handleSearchChange} /></Form.Group>
        </Col>
        <Col md={3}>
          <Form.Group>
            <Form.Label>Filter by State:</Form.Label>
            <DropdownButton id="dropdown-states-button" title={selectedStates.length > 0 ? `${selectedStates.length} states selected` : "All States"}>
              {allStates.map(state => (
                <Dropdown.Item key={state} as="div">
                  <Form.Check type="checkbox" id={`state-${state}`} label={state} checked={selectedStates.includes(state)} onChange={() => handleStateChange(state)} />
                </Dropdown.Item>
              ))}
            </DropdownButton>
          </Form.Group>
        </Col>
        <Col md={3}>
          <Form.Group>
            <Form.Label>Filter by City:</Form.Label>
            <DropdownButton id="dropdown-cities-button" title={selectedCities.length > 0 ? `${selectedCities.length} cities selected` : "All Cities"}>
              {availableCities.map(city => (
                <Dropdown.Item key={city} as="div">
                  <Form.Check type="checkbox" id={`city-${city}`} label={formatCityLabel(city)} checked={selectedCities.includes(city)} onChange={() => handleCityChange(city)} />
                </Dropdown.Item>
              ))}
            </DropdownButton>
          </Form.Group>
        </Col>
        <Col md={3}>
          <Row>
            <Col>
              <Form.Group><Form.Label>Validated:</Form.Label><Form.Select value={validatedFilter} onChange={handleValidatedFilterChange}><option value="all">All</option><option value="validated">Validated</option><option value="unvalidated">Not Validated</option></Form.Select></Form.Group>
            </Col>
            <Col>
              <Form.Group><Form.Label>Qualified:</Form.Label><Form.Select value={qualifiedFilter} onChange={handleQualifiedFilterChange}><option value="all">All</option><option value="qualified">Qualified</option><option value="unqualified">Not Qualified</option></Form.Select></Form.Group>
            </Col>
          </Row>
        </Col>
      </Row>
      {currentView === 'cities' && (
        <Row className="mb-4">
          <Col>
            <Card>
              <Card.Header><h2>CT Scan Centers by State</h2></Card.Header>
              <Card.Body>
                <div className="row">
                  {Object.entries(stateCounts).sort((a, b) => sortByStateName(a[0], b[0])).map(([state, count]) => {
                    const stateCenters = processedCenters.filter(center => resolveState(center) === state);
                    const stateCities = [...new Set(stateCenters.map(center => center.city))].sort(sortByCityName);
                    const validatedCount = stateCenters.filter(c => c.validated).length;
                    const qualifiedCount = stateCenters.filter(c => c.qualified).length;
                    const isAnyValidated = validatedCount > 0;
                    const isExpanded = expandedStates.has(state);

                    if (isExpanded) {
                      return (
                        <div key={state} className="col-12 mb-4">
                          <Card className="border-primary">
                            <Card.Header className="d-flex justify-content-between align-items-center">
                              <h5 className="mb-0">{state} ({count} centers)</h5>
                              <Button variant="outline-primary" size="sm" onClick={() => setExpandedStates(prev => { const newExpanded = new Set(prev); newExpanded.delete(state); return newExpanded; })}>Collapse</Button>
                            </Card.Header>
                            <Card.Body>
                              <div className="row">
                                {stateCities.map(city => {
                                  const displayCity = formatCityLabel(city);
                                  const cityCenters = stateCenters.filter(c => c.city === city);
                                  const cityCount = cityCenters.length;
                                  const cityValidatedCount = cityCenters.filter(c => c.validated).length;
                                  const cityQualifiedCount = cityCenters.filter(c => c.qualified).length;
                                  const cityIsAnyValidated = cityValidatedCount > 0;

                                  return (
                                    <div key={city} className="col-md-3 col-sm-4 col-6 mb-3">
                                      <Card className={`h-100 text-center ${cityIsAnyValidated ? 'border-success' : ''}`} style={{ cursor: 'pointer', border: '2px solid #dee2e6' }}>
                                        <Card.Body className="d-flex flex-column">
                                          <Card.Title className="text-primary">{displayCity}</Card.Title>
                                          <Card.Text as="div" className="mt-auto">
                                            <strong>{cityCount}</strong> CT Scan Centers<br/>
                                            <div className="d-flex justify-content-center mt-2">
                                              <div className="me-3"><div className="text-center text-success small">Validated</div><div className="d-flex justify-content-center"><CircularProgress value={cityValidatedCount} max={cityCount} size={40} color="#4CAF50" /></div></div>
                                              <div><div className="text-center text-info small">Qualified</div><div className="d-flex justify-content-center"><CircularProgress value={cityQualifiedCount} max={cityCount} size={40} color="#2196F3" /></div></div>
                                            </div>
                                          </Card.Text>
                                          <div className="d-flex justify-content-center mt-2"><Form.Check type="checkbox" id={`validate-${city}`} label="Toggle Validation" checked={cityIsAnyValidated} onChange={() => toggleCityValidation(city)} /></div>
                                          <Button variant="primary" className="mt-2" onClick={(e) => { e.stopPropagation(); handleCityClick(city); }}>View Details</Button>
                                        </Card.Body>
                                      </Card>
                                    </div>
                                  );
                                })}
                              </div>
                            </Card.Body>
                          </Card>
                        </div>
                      );
                    } else {
                      return (
                        <div key={state} className="col-md-3 col-sm-4 col-6 mb-3">
                          <Card className={`h-100 text-center text-white ${isAnyValidated ? 'border-success' : ''}`} style={{ cursor: 'pointer', border: '2px solid #dee2e6', backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), url("${getStateImage(state)}")`, backgroundSize: 'cover', backgroundPosition: 'center' }}>
                            <Card.Body className="d-flex flex-column">
                              <Card.Title>{state}</Card.Title>
                              <Card.Text as="div" className="mt-auto">
                                <strong>{count}</strong> CT Scan Centers<br/>
                                <div className="d-flex justify-content-center mt-2">
                                  <div className="me-3"><div className="text-center text-white small">Validated</div><div className="d-flex justify-content-center"><CircularProgress value={validatedCount} max={count} size={50} color="#4CAF50" /></div></div>
                                  <div><div className="text-center text-white small">Qualified</div><div className="d-flex justify-content-center"><CircularProgress value={qualifiedCount} max={count} size={50} color="#2196F3" /></div></div>
                                </div>
                                <div className="text-white mt-2">{stateCities.length} Cities</div>
                              </Card.Text>
                              <Button variant="light" className="mt-2" onClick={(e) => { e.stopPropagation(); setExpandedStates(prev => { const newExpanded = new Set(prev); newExpanded.add(state); return newExpanded; }); }}>View Cities</Button>
                            </Card.Body>
                          </Card>
                        </div>
                      );
                    }
                  })}
                </div>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {currentView === 'centers' && (
        <Row className="mb-4">
          <Col>
            <Card>
              <Card.Header><h2>CT Scan Centers in {selectedCities.join(', ')} ({sortedCenters(processedCenters.filter(c => selectedCities.includes(c.city))).length} found)</h2></Card.Header>
              <Card.Body>
                <Table striped bordered hover responsive>
                  <thead>
                    <tr>
                      <th>#</th>
                      <th onClick={() => requestSort('center_name')} style={{ cursor: 'pointer' }}>Center Name{sortConfig.key === 'center_name' && (<span>{sortConfig.direction === 'asc' ? ' ↑' : ' ↓'}</span>)}</th>
                      <th onClick={() => requestSort('city')} style={{ cursor: 'pointer' }}>City{sortConfig.key === 'city' && (<span>{sortConfig.direction === 'asc' ? ' ↑' : ' ↓'}</span>)}</th>
                      <th onClick={() => requestSort('address')} style={{ cursor: 'pointer' }}>Address{sortConfig.key === 'address' && (<span>{sortConfig.direction === 'asc' ? ' ↑' : ' ↓'}</span>)}</th>
                      <th onClick={() => requestSort('contact_details')} style={{ cursor: 'pointer' }}>Contact{sortConfig.key === 'contact_details' && (<span>{sortConfig.direction === 'asc' ? ' ↑' : ' ↓'}</span>)}</th>
                      <th onClick={() => requestSort('google_maps_link')} style={{ cursor: 'pointer' }}>Maps{sortConfig.key === 'google_maps_link' && (<span>{sortConfig.direction === 'asc' ? ' ↑' : ' ↓'}</span>)}</th>
                      <th>Notes</th>
                      <th>Validated</th>
                      <th>Qualified</th>
                      <th>Action</th>
                      <th><Form.Check type="checkbox" onChange={(e) => { const cityCenters = processedCenters.filter(c => selectedCities.includes(c.city)); if (e.target.checked) { const allIds = cityCenters.map(center => center.id); setSelectedForDeletion(new Set(allIds)); } else { setSelectedForDeletion(new Set()); } }} checked={processedCenters.filter(c => selectedCities.includes(c.city)).length > 0 && processedCenters.filter(c => selectedCities.includes(c.city)).every(center => selectedForDeletion.has(center.id))} /> Delete</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedCenters(processedCenters.filter(c => selectedCities.includes(c.city))).map((center) => {
                      const isEditing = editingCenterId === center.id;
                      const draftNote = noteDrafts[center.id] ?? center.notes ?? '';
                      const originalNote = center.notes || '';
                      const hasUnsavedNote = draftNote.trim() !== originalNote.trim();
                      const isSavingNote = noteSaving[center.id];
                      const searchResult = searchResults.find(res => res.item.id === center.id);
                      const matches = searchResult ? searchResult.matches : [];
                      const getMatches = (key) => { const match = matches.find(m => m.key === key); return match ? match.indices : []; };

                      return (
                        <tr key={center.id}>
                          <td>{center.id}</td>
                          <td>{isEditing ? <Form.Control value={editFormData?.center_name ?? ''} onChange={(e) => handleEditFieldChange('center_name', e.target.value)} /> : <HighlightedText text={center.center_name} indices={getMatches('center_name')} />}</td>
                          <td>{isEditing ? <Form.Control value={editFormData?.city ?? ''} onChange={(e) => handleEditFieldChange('city', e.target.value)} /> : <HighlightedText text={center.city} indices={getMatches('city')} />}</td>
                          <td>{isEditing ? <Form.Control as="textarea" rows={3} value={editFormData?.address ?? ''} onChange={(e) => handleEditFieldChange('address', e.target.value)} /> : <HighlightedText text={center.address} indices={getMatches('address')} />}</td>
                          <td>{isEditing ? <Form.Control as="textarea" rows={2} value={editFormData?.contact_details ?? ''} onChange={(e) => handleEditFieldChange('contact_details', e.target.value)} /> : (center.contact_details && center.contact_details.trim() !== '' && center.contact_details !== 'Not provided in text' && center.contact_details !== 'Information not available.' && center.contact_details !== 'No phone number available.' ? center.contact_details : <span className="text-danger">No contact info</span>)}</td>
                          <td>{isEditing ? <Form.Control value={editFormData?.google_maps_link ?? ''} onChange={(e) => handleEditFieldChange('google_maps_link', e.target.value)} placeholder="https://" /> : (center.google_maps_link ? <a href={center.google_maps_link} target="_blank" rel="noopener noreferrer">View Map</a> : <span className="text-muted">No map link</span>)}</td>
                          <td>{isEditing ? <Form.Control as="textarea" rows={2} value={editFormData?.notes ?? ''} onChange={(e) => handleEditFieldChange('notes', e.target.value)} placeholder="Add notes for this center" /> : (<><Form.Control as="textarea" rows={2} value={draftNote} onChange={(e) => handleNoteChange(center.id, e.target.value)} placeholder="Add notes for this center" /><div className="mt-2 d-flex align-items-center"><Button variant="success" size="sm" disabled={isSavingNote || !hasUnsavedNote} onClick={() => handleSaveNote(center)}>{isSavingNote ? <Spinner as="span" animation="border" size="sm" /> : 'Save Note'}</Button>{hasUnsavedNote && <small className="ms-2 text-muted">Unsaved changes</small>}</div></>)}</td>
                          <td>{isEditing ? <Form.Check type="switch" id={`validated-switch-${center.id}`} checked={editFormData?.validated ?? false} onChange={(e) => handleEditFieldChange('validated', e.target.checked)} /> : <Form.Check type="switch" id={`validated-switch-display-${center.id}`} checked={center.validated} onChange={() => handleValidationToggle(center.id, !center.validated)} />}</td>
                          <td>{isEditing ? <Form.Check type="switch" id={`qualified-switch-${center.id}`} checked={editFormData?.qualified ?? false} onChange={(e) => handleEditFieldChange('qualified', e.target.checked)} /> : <Form.Check type="switch" id={`qualified-switch-display-${center.id}`} checked={center.qualified} onChange={() => handleQualificationToggle(center.id, !center.qualified)} />}</td>
                          <td>{isEditing ? (<><Button variant="success" size="sm" onClick={handleSaveEdit}>Save</Button><Button variant="secondary" size="sm" className="ms-2" onClick={handleCancelEdit}>Cancel</Button></>) : (<Button variant="primary" size="sm" onClick={() => handleEditClick(center)}>Edit</Button>)}</td>
                          <td><Form.Check type="checkbox" id={`delete-checkbox-${center.id}`} checked={selectedForDeletion.has(center.id)} onChange={(e) => { const newSelected = new Set(selectedForDeletion); if (e.target.checked) { newSelected.add(center.id); } else { newSelected.delete(center.id); } setSelectedForDeletion(newSelected); }} /></td>
                        </tr>
                      );
                    })}
                  </tbody>
                </Table>
                {selectedForDeletion.size > 0 && (<Button variant="danger" onClick={() => setShowDeleteModal(true)}>Delete Selected ({selectedForDeletion.size})</Button>)}
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      <Row className="mb-4">
        <Col md={6}>
          <Card className="h-100">
            <Card.Header><h2>Upload New Data</h2></Card.Header>
            <Card.Body>
              <Form.Group><Form.Label>Upload CSV file:</Form.Label><Form.Control type="file" accept=".csv" onChange={handleFileChange} /></Form.Group>
              <Button variant="primary" className="mt-3" onClick={handleFileUpload} disabled={isUploading || !file}>{isUploading ? 'Uploading...' : 'Upload'}</Button>
              {uploadProgress !== null && (<ProgressBar now={uploadProgress} label={`${uploadProgress}%`} className="mt-3" />)}
              {uploadStatusMessage && (<Alert variant="info" className="mt-3">{uploadStatusMessage}</Alert>)}
            </Card.Body>
          </Card>
        </Col>
        <Col md={6}>
          <Card className="h-100">
            <Card.Header><h2>Data Maintenance</h2></Card.Header>
            <Card.Body>
              <p>Remove duplicate records from the database. This action is based on exact address matches and cannot be undone.</p>
              <Button variant="danger" onClick={handleRemoveDuplicates}>Remove Exact Duplicates</Button>
              <hr />
              <p>Review records that are very similar but not identical. You can manually merge them.</p>
              <Button variant="warning" onClick={handleFindPotentialDuplicates} disabled={isFindingDuplicates}>{isFindingDuplicates ? <Spinner as="span" animation="border" size="sm" /> : 'Review Similar Duplicates'}</Button>
              <hr />
              <p>Automatically merge all similar records based on the defined strategy (keeps the record with the lower ID). This is a bulk operation.</p>
              <Button variant="info" onClick={handleAutoMergeDuplicates} disabled={isAutoMerging}>{isAutoMerging ? <Spinner as="span" animation="border" size="sm" /> : 'Auto-Merge All Duplicates'}</Button>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)}>
        <Modal.Header closeButton><Modal.Title>Confirm Deletion</Modal.Title></Modal.Header>
        <Modal.Body>Are you sure you want to delete {selectedForDeletion.size} selected centers? This action cannot be undone.</Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>Cancel</Button>
          <Button variant="danger" onClick={async () => {
            for (const centerId of selectedForDeletion) {
              try { await axios.delete(`${API_BASE_URL}/api/centers/${centerId}`); } catch (error) { console.error(`Error deleting center ${centerId}:`, error); }
            }
            alert(`${selectedForDeletion.size} centers deleted successfully.`);
            setSelectedForDeletion(new Set());
            setShowDeleteModal(false);
            fetchCenters();
          }}>Delete</Button>
        </Modal.Footer>
      </Modal>

      {potentialDuplicates.length > 0 && (
        <Modal show={showDuplicateModal} onHide={() => setShowDuplicateModal(false)} size="xl">
          <Modal.Header closeButton><Modal.Title>Review Potential Duplicates ({currentDuplicateIndex + 1} of {potentialDuplicates.length})</Modal.Title></Modal.Header>
          <Modal.Body>
            <p>These two records have a similarity score of <strong>{potentialDuplicates[currentDuplicateIndex].similarity_score}%</strong>. Please review them and decide whether to merge or ignore.</p>
            <Row>
              <Col md={6}>
                <Card>
                  <Card.Header>Record 1 (ID: {potentialDuplicates[currentDuplicateIndex].center1.id})</Card.Header>
                  <Card.Body>
                    <p><strong>Name:</strong> {potentialDuplicates[currentDuplicateIndex].center1.center_name}</p>
                    <p><strong>Address:</strong> {potentialDuplicates[currentDuplicateIndex].center1.address}</p>
                    <p><strong>Contact:</strong> {potentialDuplicates[currentDuplicateIndex].center1.contact_details}</p>
                    <p><strong>Notes:</strong> {potentialDuplicates[currentDuplicateIndex].center1.notes}</p>
                  </Card.Body>
                  <Card.Footer><Button variant="success" onClick={() => handleMergeDuplicates(potentialDuplicates[currentDuplicateIndex].center1.id, potentialDuplicates[currentDuplicateIndex].center2.id)}>Keep This One</Button></Card.Footer>
                </Card>
              </Col>
              <Col md={6}>
                <Card>
                  <Card.Header>Record 2 (ID: {potentialDuplicates[currentDuplicateIndex].center2.id})</Card.Header>
                  <Card.Body>
                    <p><strong>Name:</strong> {potentialDuplicates[currentDuplicateIndex].center2.center_name}</p>
                    <p><strong>Address:</strong> {potentialDuplicates[currentDuplicateIndex].center2.address}</p>
                    <p><strong>Contact:</strong> {potentialDuplicates[currentDuplicateIndex].center2.contact_details}</p>
                    <p><strong>Notes:</strong> {potentialDuplicates[currentDuplicateIndex].center2.notes}</p>
                  </Card.Body>
                  <Card.Footer><Button variant="success" onClick={() => handleMergeDuplicates(potentialDuplicates[currentDuplicateIndex].center2.id, potentialDuplicates[currentDuplicateIndex].center1.id)}>Keep This One</Button></Card.Footer>
                </Card>
              </Col>
            </Row>
          </Modal.Body>
          <Modal.Footer><Button variant="secondary" onClick={handleIgnoreDuplicate}>Ignore (Not a Duplicate)</Button></Modal.Footer>
        </Modal>
      )}

    </Container>
  );
}

export default App;
