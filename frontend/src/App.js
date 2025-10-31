import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Container, Row, Col, Table, Form, Button, Card, Alert, Modal } from 'react-bootstrap';
import { Bar, Pie, Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement } from 'chart.js';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default marker icons in Leaflet with React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend);

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5050';

function App() {
  const [centers, setCenters] = useState([]);
  const [file, setFile] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCity, setSelectedCity] = useState('');
  const [cities, setCities] = useState([]);
  const [contactType, setContactType] = useState('all'); // 'all', 'hasContact', 'noContact'
  const [validatedFilter, setValidatedFilter] = useState('all'); // 'all', 'validated', 'unvalidated'
  const [qualifiedFilter, setQualifiedFilter] = useState('all'); // 'all', 'qualified', 'unqualified'
  const [showStats, setShowStats] = useState(false);
  const [currentView, setCurrentView] = useState('cities'); // 'cities' or 'centers'
  const [selectedCityCenters, setSelectedCityCenters] = useState([]);
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [cityStats, setCityStats] = useState(null); // State to store city stats
  const [editingCenterId, setEditingCenterId] = useState(null);
  const [editFormData, setEditFormData] = useState(null);
  const [noteDrafts, setNoteDrafts] = useState({});
  const [noteSaving, setNoteSaving] = useState({});
  const [selectedForDeletion, setSelectedForDeletion] = useState(new Set());
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  const fetchCityStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/cities/stats`);
      setCityStats(response.data);
    } catch (error) {
      console.error('Error fetching city stats:', error);
    }
  };

  useEffect(() => {
    fetchCenters();
    fetchCityStats();
  }, []);

  const fetchCenters = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/centers`);
      setCenters(response.data);
      
      // Get unique cities for filter dropdown
      const uniqueCities = [...new Set(response.data.map(center => center.city))];
      setCities(uniqueCities);

      const initialNotes = {};
      response.data.forEach(center => {
        initialNotes[center.id] = center.notes || '';
      });
      setNoteDrafts(initialNotes);
      setNoteSaving({});
    } catch (error) {
      console.error('Error fetching centers:', error);
    }
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleFileUpload = async () => {
    if (!file) {
      alert('Please select a file to upload.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      await axios.post(`${API_BASE_URL}/api/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      alert('File uploaded successfully!');
      fetchCenters(); // Refresh data after upload
      fetchCityStats(); // Refresh city stats after upload
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Error uploading file.');
    }
  };

  const handleRemoveDuplicates = async () => {
    if (window.confirm("Are you sure you want to remove duplicate records based on address? This cannot be undone.")) {
      try {
        const response = await axios.delete(`${API_BASE_URL}/api/deduplicate`);
        alert(`Removed ${response.data.duplicates_removed} duplicate records`);
        fetchCenters(); // Refresh the data
        fetchCityStats(); // Refresh city stats after deduplication
      } catch (error) {
        console.error('Error removing duplicates:', error);
        alert('Error removing duplicates');
      }
    }
  };

  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  const handleCityChange = (e) => {
    setSelectedCity(e.target.value);
  };

  const handleContactTypeChange = (e) => {
    setContactType(e.target.value);
  };

  const handleValidatedFilterChange = (e) => {
    setValidatedFilter(e.target.value);
  };

  const handleQualifiedFilterChange = (e) => {
    setQualifiedFilter(e.target.value);
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
    setEditFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleCancelEdit = () => {
    setEditingCenterId(null);
    setEditFormData(null);
  };

  const handleSaveEdit = async () => {
    if (!editingCenterId || !editFormData) {
      return;
    }

    try {
      await axios.put(`${API_BASE_URL}/api/centers/${editingCenterId}`, {
        ...editFormData,
      });
      alert('Center updated successfully');
      setEditingCenterId(null);
      setEditFormData(null);
      fetchCenters();
      fetchCityStats();
    } catch (error) {
      console.error('Error updating center:', error);
      alert('Error updating center');
    }
  };

  const handleNoteChange = (centerId, value) => {
    setNoteDrafts((prev) => ({
      ...prev,
      [centerId]: value,
    }));
  };

  const handleSaveNote = async (center) => {
    const noteContent = noteDrafts[center.id] ?? '';
    try {
      setNoteSaving((prev) => ({ ...prev, [center.id]: true }));
      const response = await axios.patch(`${API_BASE_URL}/api/centers/${center.id}/notes`, {
        notes: noteContent,
      });
      const updatedCenter = response.data;
      setCenters((prev) =>
        prev.map((item) => (item.id === center.id ? updatedCenter : item))
      );
      setNoteDrafts((prev) => ({
        ...prev,
        [center.id]: updatedCenter.notes || '',
      }));
    } catch (error) {
      console.error('Error updating notes:', error);
      alert('Error updating notes');
    } finally {
      setNoteSaving((prev) => ({ ...prev, [center.id]: false }));
    }
  };

  // Function to toggle validation status for a center
  const handleValidationToggle = async (centerId, validated) => {
    try {
      await axios.put(`${API_BASE_URL}/api/centers/${centerId}/validate`, {}, {
        params: {
          validated: validated
        }
      });
      // Refresh the data
      fetchCenters();
    } catch (error) {
      console.error('Error updating validation status:', error);
      alert('Error updating validation status');
    }
  };

  // Function to toggle qualification status for a center
  const handleQualificationToggle = async (centerId, qualified) => {
    try {
      await axios.put(`${API_BASE_URL}/api/centers/${centerId}/qualify`, {}, {
        params: {
          qualified: qualified
        }
      });
      // Refresh the data
      fetchCenters();
    } catch (error) {
      console.error('Error updating qualification status:', error);
      alert('Error updating qualification status');
    }
  };

  // Function to delete a specific center
  const handleDeleteCenter = async (centerId, centerName) => {
    if (window.confirm(`Are you sure you want to delete the center "${centerName}"? This cannot be undone.`)) {
      try {
        await axios.delete(`${API_BASE_URL}/api/centers/${centerId}`);
        alert('Center deleted successfully');
        fetchCenters(); // Refresh the data
      } catch (error) {
        console.error('Error deleting center:', error);
        alert('Error deleting center');
      }
    }
  };

  // Function to toggle city validation status
  const toggleCityValidation = async (city) => {
    try {
      // First, let's check if any centers in this city are already validated to determine toggle state
      const centersInCity = centers.filter(c => c.city === city);
      if (centersInCity.length === 0) {
        alert(`No centers found for city ${city}`);
        return;
      }

      // Determine new validation status based on current status
      // We'll toggle the first center's status to determine the new state for all in the city
      const currentStatus = centersInCity[0].validated;
      const newValidatedStatus = !currentStatus;

      await axios.put(`${API_BASE_URL}/api/cities/${encodeURIComponent(city)}/validate`, {}, {
        params: {
          validated: newValidatedStatus
        }
      });
      
      alert(`City ${city} validation status updated to ${newValidatedStatus ? 'Validated' : 'Not Validated'}`);
      fetchCenters(); // Refresh the data
    } catch (error) {
      console.error('Error updating city validation status:', error);
      alert('Error updating city validation status');
    }
  };

  // State to store geocoded coordinates
  const [geocodedCoords, setGeocodedCoords] = useState({});
  const [allCityCoords, setAllCityCoords] = useState({});

  // Function to get coordinates for Indian cities with a comprehensive predefined list
  const getCityCoordinates = (city) => {
    // Comprehensive map of Indian cities and their approximate coordinates
    const cityCoords = {
      'Kolhapur': [16.6959, 74.2246],
      'Jalgaon': [20.9962, 75.6959],
      'Aurangabad': [19.8762, 75.3433],
      'Nagpur': [21.1458, 79.0882],
      'Nashik': [19.9975, 73.7898],
      'Pune': [18.5204, 73.8567],
      'Mumbai': [19.0760, 72.8777],
      'Ahmednagar': [19.0900, 74.7400],
      'Latur': [18.4000, 76.5600],
      'Beed': [18.5800, 75.7800],
      'Sangli': [16.8500, 74.5700],
      'Satara': [17.6799, 74.0266],
      'Sindhudurg': [16.0432, 73.4199],
      'Ratnagiri': [17.9995, 73.3186],
      'Raigad': [18.5194, 73.2233],
      'Thane': [19.2183, 72.9781],
      'Bhandara': [21.1808, 79.6165],
      'Gondia': [21.4981, 80.1976],
      'Chandrapur': [19.9642, 79.2963],
      'Yavatmal': [20.3893, 78.1405],
      'Wardha': [20.7421, 78.5959],
      'Amravati': [20.9389, 77.7481],
      'Akola': [20.7186, 77.0031],
      'Buldhana': [20.5633, 76.1809],
      'Washim': [20.9325, 77.6507],
      'Hingoli': [19.6770, 77.1575],
      'Parbhani': [19.2698, 76.7708],
      'Jalna': [19.8553, 75.8425],
      'Osmanabad': [18.1682, 76.0542],
      'Nanded': [19.1500, 77.3000],
      'Solapur': [17.6599, 75.9064],
      'Chhatrapati Sambhajinagar': [19.8762, 75.3433],
      'Ahilyanagar': [18.5800, 75.7800],
      'Bhusawal': [21.0450, 75.7800],
      'Chalisgaon': [20.3140, 75.3160],
      'Chopda': [21.2400, 75.6900],
      'Ichalkaranji': [16.6950, 74.4650],
      'Jaysingpur': [16.1600, 74.5800],
      'Kagal': [16.4000, 74.3000],
      'Kopargaon': [19.8800, 74.5000],
      'Kudal': [15.9500, 73.7000],
      'Miraj': [16.8600, 74.6500],
      'Mira Bhayandar': [19.2800, 72.8500],
      'Navi Mumbai': [19.0330, 73.0290],
      'Pachora': [20.5900, 75.6700],
      'Palus': [17.0000, 74.5000],
      'Parli': [18.8500, 76.5000],
      'Pathardi': [19.5000, 75.0000],
      'Sangamner': [19.6000, 74.2000],
      'Shirdi': [19.7600, 74.5000],
      'Shirpur': [21.3000, 75.5000],
      'Shrigonda': [17.1000, 74.7000],
      'Shrirampur': [19.5000, 74.2000],
      'Tasgaon': [17.0000, 74.8000],
      'Uran': [18.9000, 72.9500],
      'Vaijapur': [20.0000, 75.2000],
      'Vasai-Virar': [19.4000, 72.8000],
      'Wardha': [20.7500, 78.6000],
      'Yavatmal': [20.4000, 78.1500],
      'Amalner': [21.0500, 75.8500],
      'Baramati': [18.1500, 74.6000],
      'Barshi': [18.2500, 75.7000],
      'Chinchwad': [18.6000, 73.8000],
      'Dehu Road': [18.7500, 73.8000],
      'Hadapsar': [18.5000, 73.9500],
      'Hinjewadi': [18.5800, 73.7200],
      'Jejuri': [18.3000, 74.2000],
      'Khadkale': [18.4000, 74.3000],
      'Khed': [18.6000, 73.4000],
      'Lonavala': [18.7500, 73.4000],
      'Mhaswad': [17.9000, 74.1000],
      'Pimpri-Chinchwad': [18.6000, 73.8000],
      'Sangli-Miraj-Kupwad': [16.8500, 74.6000],
      'Shikrapur': [18.4000, 73.9000],
      'Vadgaon': [18.5000, 73.8500],
      'Vadodara': [22.3072, 73.1812],
      'Ambajogai': [18.7000, 76.5000],
      'Ashti': [18.4000, 76.1000],
      'Bhadravati': [17.0000, 74.5000],
      'Darwha': [18.8000, 77.3000],
      'Deglur': [19.1000, 77.6000],
      'Gadhinglaj': [16.5000, 74.2000],
      'Hatkanangle': [16.8000, 74.3000],
      'Islampur': [16.8000, 74.3000],
      'Jath': [16.7500, 74.5000],
      'Kankavli': [16.1000, 73.7000],
      'Karad': [17.2800, 74.2000],
      'Khadkoli': [16.5000, 74.3000],
      'Khatav': [17.5000, 73.9000],
      'Koregaon': [17.3500, 74.1000],
      'Madangad': [17.0000, 73.5000],
      'Mahabaleshwar': [17.9200, 73.6500],
      'Mahad': [18.0800, 73.4200],
      'Malegaon': [20.5500, 74.5000],
      'Malwan': [16.0500, 73.4500],
      'Manchar': [19.0000, 73.8000],
      'Mangaon': [18.6000, 73.2000],
      'Mangrulpir': [19.3000, 77.1000],
      'Mhasla': [17.8000, 73.3000],
      'Mumbai City': [18.9200, 72.8300],
      'Nagothane': [18.3500, 73.2000],
      'Nandgaon': [19.9000, 74.0000],
      'Niphad': [20.0000, 74.2000],
      'Ozar': [20.2000, 73.9000],
      'Pandharpur': [17.6800, 75.3200],
      'Pen': [18.7300, 73.1200],
      'Phaltan': [17.9000, 74.5000],
      'Sangameshwar': [17.2000, 73.1000],
      'Shahada': [21.5000, 74.5000],
      'Shegaon': [20.8000, 76.5000],
      'Shirala': [16.9000, 74.8000],
      'Shirur': [18.1500, 74.4000],
      'Talegaon Dabhade': [18.7300, 73.7000],
      'Tarapur': [19.8500, 72.6500],
      'Vita': [17.1000, 73.8000],
      'Wai': [17.9800, 73.8000],
      'Walchandnagar': [18.5800, 74.5500],
      'Warora': [19.8300, 79.0000],
      'Yaval': [21.2000, 75.8000],
      'कोल्हापूर': [16.6959, 74.2246], // Kolhapur in Marathi
      'Okay, I understand. Since you haven\'t provided an address, I can\'t extract a': [20.5937, 78.9629], // Default for invalid entries
      // Add default coordinates as fallback
      'default': [20.5937, 78.9629] // Center of India
    };

    // Normalize city name to handle cases like 'Kolhapur' vs 'Kolhapur '
    const normalizedCity = city.trim();
    
    // Handle empty or invalid city names
    if (!normalizedCity || normalizedCity === '') {
      return cityCoords['default'];
    }
    
    // Find the city in the map (exact match first)
    if (cityCoords[normalizedCity]) {
      return cityCoords[normalizedCity];
    }
    
    // Try case insensitive match
    for (const [key, value] of Object.entries(cityCoords)) {
      if (key.toLowerCase() === normalizedCity.toLowerCase()) {
        return value;
      }
    }

    // Return a default location (India center) if city not found
    return cityCoords['default'];
  };

  // Sorting functions
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

        // Handle special fields that might be nested or transformed
        if (sortConfig.key === 'contact_status') {
          aValue = (a.contact_details && a.contact_details.trim() !== '' && a.contact_details !== 'Not provided in text' && a.contact_details !== 'Information not available.' && a.contact_details !== 'No phone number available.');
          bValue = (b.contact_details && b.contact_details.trim() !== '' && b.contact_details !== 'Not provided in text' && b.contact_details !== 'Information not available.' && b.contact_details !== 'No phone number available.');
        } else if (sortConfig.key === 'maps_status') {
          aValue = a.google_maps_link && a.google_maps_link.trim() !== '';
          bValue = b.google_maps_link && b.google_maps_link.trim() !== '';
        }

        // Convert to lowercase for string comparison
        if (typeof aValue === 'string') aValue = aValue.toLowerCase();
        if (typeof bValue === 'string') bValue = bValue.toLowerCase();

        // Handle boolean values
        if (typeof aValue === 'boolean' && typeof bValue === 'boolean') {
          return sortConfig.direction === 'asc' ? (aValue === bValue ? 0 : aValue ? -1 : 1) : (aValue === bValue ? 0 : aValue ? 1 : -1);
        }

        // Handle numeric comparisons
        if (!isNaN(Number(aValue)) && !isNaN(Number(bValue))) {
          const numA = Number(aValue);
          const numB = Number(bValue);
          if (sortConfig.direction === 'asc') {
            return numA < numB ? -1 : numA > numB ? 1 : 0;
          } else {
            return numA > numB ? -1 : numA < numB ? 1 : 0;
          }
        }

        // Handle string comparisons
        if (sortConfig.direction === 'asc') {
          return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
        } else {
          return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
        }
      });
    }
    return sortableData;
  };

  const matchesValidatedSelection = (center) => {
    if (validatedFilter === 'validated') {
      return center.validated;
    }
    if (validatedFilter === 'unvalidated') {
      return !center.validated;
    }
    return true;
  };

  const matchesQualifiedSelection = (center) => {
    if (qualifiedFilter === 'qualified') {
      return center.qualified;
    }
    if (qualifiedFilter === 'unqualified') {
      return !center.qualified;
    }
    return true;
  };

  // Filter centers based on search term, selected city, and contact type
  const filteredCenters = centers.filter((center) => {
    const matchesSearch = 
      center.center_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      center.city.toLowerCase().includes(searchTerm.toLowerCase()) ||
      center.address.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesCity = selectedCity ? center.city === selectedCity : true;
    
    let matchesContactType = true;
    if (contactType === 'hasContact') {
      matchesContactType = center.contact_details && center.contact_details.trim() !== '' && center.contact_details !== 'Not provided in text' && center.contact_details !== 'Information not available.' && center.contact_details !== 'No phone number available.';
    } else if (contactType === 'noContact') {
      matchesContactType = !center.contact_details || center.contact_details.trim() === '' || center.contact_details === 'Not provided in text' || center.contact_details === 'Information not available.' || center.contact_details === 'No phone number available.';
    }
    
    return matchesSearch && matchesCity && matchesContactType && matchesValidatedSelection(center) && matchesQualifiedSelection(center);
  });

  // Filter centers by city for drill-down view
  const filteredCentersByCity = centers.filter((center) => {
    const matchesSearch = 
      center.center_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      center.city.toLowerCase().includes(searchTerm.toLowerCase()) ||
      center.address.toLowerCase().includes(searchTerm.toLowerCase());
    
    let matchesContactType = true;
    if (contactType === 'hasContact') {
      matchesContactType = center.contact_details && center.contact_details.trim() !== '' && center.contact_details !== 'Not provided in text' && center.contact_details !== 'Information not available.' && center.contact_details !== 'No phone number available.';
    } else if (contactType === 'noContact') {
      matchesContactType = !center.contact_details || center.contact_details.trim() === '' || center.contact_details === 'Not provided in text' || center.contact_details === 'Information not available.' || center.contact_details === 'No phone number available.';
    }
    
    return matchesSearch && matchesContactType && matchesValidatedSelection(center) && matchesQualifiedSelection(center);
  });

  // Get city-specific centers for drill-down
  const getCityCenters = (city) => {
    let filtered = centers.filter(center => 
      center.city.toLowerCase().includes(city.toLowerCase()) &&
      (searchTerm === '' || 
        center.center_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        center.address.toLowerCase().includes(searchTerm.toLowerCase()))
    );
    filtered = filtered.filter((center) => matchesValidatedSelection(center) && matchesQualifiedSelection(center));
    
    // Apply sorting to the filtered data
    return sortedCenters(filtered);
  };

  // Apply sorting to all filtered centers
  const getSortedFilteredCenters = () => {
    let filtered = centers.filter((center) => {
      const matchesSearch = 
        center.center_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        center.city.toLowerCase().includes(searchTerm.toLowerCase()) ||
        center.address.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesCity = selectedCity ? center.city === selectedCity : true;
      
      let matchesContactType = true;
      if (contactType === 'hasContact') {
        matchesContactType = center.contact_details && center.contact_details.trim() !== '' && center.contact_details !== 'Not provided in text' && center.contact_details !== 'Information not available.' && center.contact_details !== 'No phone number available.';
      } else if (contactType === 'noContact') {
        matchesContactType = !center.contact_details || center.contact_details.trim() === '' || center.contact_details === 'Not provided in text' || center.contact_details === 'Information not available.' || center.contact_details === 'No phone number available.';
      }
      
      return matchesSearch && matchesCity && matchesContactType && matchesValidatedSelection(center) && matchesQualifiedSelection(center);
    });
    
    return sortedCenters(filtered);
  };

  // Analytics calculations
  const cityCounts = filteredCenters.reduce((acc, center) => {
    acc[center.city] = (acc[center.city] || 0) + 1;
    return acc;
  }, {});

  const contactStatus = filteredCenters.reduce((acc, center) => {
    if (center.contact_details && center.contact_details.trim() !== '' && center.contact_details !== 'Not provided in text' && center.contact_details !== 'Information not available.' && center.contact_details !== 'No phone number available.') {
      acc.available = (acc.available || 0) + 1;
    } else {
      acc.unavailable = (acc.unavailable || 0) + 1;
    }
    return acc;
  }, { available: 0, unavailable: 0 });

  const centersWithLinks = filteredCenters.filter(center => 
    center.google_maps_link && center.google_maps_link.trim() !== ''
  );

  // Chart data - sort cities alphabetically
  const sortedCityEntries = Object.entries(cityCounts).sort((a, b) => a[0].localeCompare(b[0]));
  const sortedCities = sortedCityEntries.map(entry => entry[0]);
  const sortedCounts = sortedCityEntries.map(entry => entry[1]);

  const cityChartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'CT Scan Centers by City'
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Number of Centers'
        }
      },
      x: {
        title: {
          display: true,
          text: 'Cities'
        }
      }
    }
  };

  const contactChartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Contact Information Availability'
      }
    }
  };

  const cityChartData = {
    labels: sortedCities,
    datasets: [
      {
        label: '# of Centers',
        data: sortedCounts,
        backgroundColor: [
          'rgba(255, 99, 132, 0.6)',
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 205, 86, 0.6)',
          'rgba(75, 192, 192, 0.6)',
          'rgba(153, 102, 255, 0.6)',
          'rgba(255, 159, 64, 0.6)',
        ],
        borderColor: [
          'rgba(255, 99, 132, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 205, 86, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(153, 102, 255, 1)',
          'rgba(255, 159, 64, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const contactChartData = {
    labels: ['With Contact Info', 'Without Contact Info'],
    datasets: [
      {
        label: 'Contact Status',
        data: [contactStatus.available, contactStatus.unavailable],
        backgroundColor: [
          'rgba(75, 192, 192, 0.6)',
          'rgba(255, 99, 132, 0.6)',
        ],
        borderColor: [
          'rgba(75, 192, 192, 1)',
          'rgba(255, 99, 132, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const stats = {
    totalCenters: filteredCenters.length,
    centersWithContact: contactStatus.available,
    centersWithoutContact: contactStatus.unavailable,
    centersWithMaps: centersWithLinks.length,
    citiesCount: Object.keys(cityCounts).length
  };

  // Handle city selection for drill-down
  const handleCityClick = (city) => {
    setSelectedCity(city);
    setSelectedCityCenters(getCityCenters(city));
    setCurrentView('centers');
  };

  // Go back to city view
  const handleBackToCities = () => {
    setCurrentView('cities');
    setSelectedCity('');
  };

  return (
    <Container fluid>
      <h1 className="my-4 text-center">
        {currentView === 'cities' ? 'CT Scan Centers Analytics Dashboard' : `CT Scan Centers in ${selectedCity}`}
      </h1>
      
      {/* Navigation and Summary Stats */}
      <Row className="mb-4">
        {currentView === 'centers' && (
          <Col md={12} className="mb-3">
            <Button variant="secondary" onClick={handleBackToCities}>
              &larr; Back to Cities
            </Button>
          </Col>
        )}
        <Col md={2}>
          <Card className="text-center bg-primary text-white">
            <Card.Body>
              <Card.Title>{stats.totalCenters}</Card.Title>
              <Card.Text>Total Centers</Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={2}>
          <Card className="text-center bg-success text-white">
            <Card.Body>
              <Card.Title>{stats.centersWithContact}</Card.Title>
              <Card.Text>With Contacts</Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={2}>
          <Card className="text-center bg-danger text-white">
            <Card.Body>
              <Card.Title>{stats.centersWithoutContact}</Card.Title>
              <Card.Text>Without Contacts</Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={2}>
          <Card className="text-center bg-info text-white">
            <Card.Body>
              <Card.Title>{stats.centersWithMaps}</Card.Title>
              <Card.Text>With Maps</Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={2}>
          <Card className="text-center bg-warning text-dark">
            <Card.Body>
              <Card.Title>{stats.citiesCount}</Card.Title>
              <Card.Text>Locations</Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={2}>
          <Card className="text-center bg-secondary text-white">
            <Card.Body>
              <Card.Title>
                <Button variant="link" className="p-0 text-white" onClick={() => setShowStats(!showStats)}>
                  {showStats ? 'Hide' : 'Show'} Details
                </Button>
              </Card.Title>
              <Card.Text>Analytics</Card.Text>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* India Map Visualization - only show in city view */}
      {currentView === 'cities' && (
        <Row className="mb-4">
          <Col>
            <Card>
              <Card.Header>
                <h2>CT Scan Centers Location Map</h2>
              </Card.Header>
              <Card.Body>
                <MapContainer 
                  center={[20.5937, 78.9629]} 
                  zoom={5} 
                  style={{ height: '400px', width: '100%' }}
                  scrollWheelZoom={true}
                >
                  <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  {Object.entries(cityCounts).map(([city, count]) => {
                    const coords = getCityCoordinates(city);
                    return (
                      <Marker 
                        key={city} 
                        position={coords}
                        eventHandlers={{
                          click: () => handleCityClick(city),
                        }}
                      >
                        <Popup>
                          <div>
                            <strong>{city}</strong><br />
                            {count} CT Scan Centers<br />
                            <Button 
                              variant="primary" 
                              size="sm" 
                              onClick={() => handleCityClick(city)}
                            >
                              View Details
                            </Button>
                          </div>
                        </Popup>
                      </Marker>
                    );
                  })}
                </MapContainer>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}
      
      {/* Filters Row */}
      <Row className="mb-4">
        <Col md={3}>
          <Form.Group>
            <Form.Label>Search by name, city, or address:</Form.Label>
            <Form.Control
              type="text"
              placeholder="Enter search term"
              value={searchTerm}
              onChange={handleSearchChange}
            />
          </Form.Group>
        </Col>
        <Col md={3}>
          <Form.Group>
            <Form.Label>Filter by City:</Form.Label>
            <Form.Select value={selectedCity} onChange={handleCityChange}>
              <option value="">All Cities</option>
              {cities.map(city => (
                <option key={city} value={city}>{city}</option>
              ))}
            </Form.Select>
          </Form.Group>
        </Col>
        <Col md={2}>
          <Form.Group>
            <Form.Label>Contact Information:</Form.Label>
            <Form.Select value={contactType} onChange={handleContactTypeChange}>
              <option value="all">All Centers</option>
              <option value="hasContact">Has Contact Info</option>
              <option value="noContact">No Contact Info</option>
            </Form.Select>
          </Form.Group>
        </Col>
        <Col md={2}>
          <Form.Group>
            <Form.Label>Validated:</Form.Label>
            <Form.Select value={validatedFilter} onChange={handleValidatedFilterChange}>
              <option value="all">All</option>
              <option value="validated">Validated Only</option>
              <option value="unvalidated">Not Validated</option>
            </Form.Select>
          </Form.Group>
        </Col>
        <Col md={2}>
          <Form.Group>
            <Form.Label>Qualified:</Form.Label>
            <Form.Select value={qualifiedFilter} onChange={handleQualifiedFilterChange}>
              <option value="all">All</option>
              <option value="qualified">Qualified Only</option>
              <option value="unqualified">Not Qualified</option>
            </Form.Select>
          </Form.Group>
        </Col>
      </Row>

      {/* Charts Row - removed as per user request */}

      {/* Additional Charts Row - removed as per user request */}

      {/* City Tiles view */}
      {currentView === 'cities' && (
        <Row className="mb-4">
          <Col>
            <Card>
              <Card.Header>
                <h2>CT Scan Centers by City</h2>
              </Card.Header>
              <Card.Body>
                <div className="row">
                  {Object.entries(cityCounts)
                    .sort((a, b) => a[0].localeCompare(b[0])) // Sort alphabetically by city name
                    .map(([city, count]) => {
                      // Get statistics for this city
                      const cityCenters = centers.filter(c => c.city === city);
                      const validatedCount = cityCenters.filter(c => c.validated).length;
                      const qualifiedCount = cityCenters.filter(c => c.qualified).length;
                      const isAnyValidated = validatedCount > 0;
                      return (
                    <div key={city} className="col-md-3 col-sm-4 col-6 mb-3">
                      <Card 
                        className={`h-100 text-center ${isAnyValidated ? 'border-success' : ''}`} 
                        style={{ cursor: 'pointer', border: '2px solid #dee2e6' }}
                      >
                        <Card.Body className="d-flex flex-column">
                          <Card.Title className="text-primary">{city}</Card.Title>
                          <Card.Text className="mt-auto">
                            <strong>{count}</strong> CT Scan Centers<br/>
                            <span className="text-success">✓ {validatedCount} Validated</span><br/>
                            <span className="text-info">★ {qualifiedCount} Qualified</span>
                          </Card.Text>
                          <Form className="mt-2">
                            <Form.Check 
                              type="checkbox"
                              id={`validate-${city}`}
                              label="Validated"
                              checked={isAnyValidated}
                              onChange={() => toggleCityValidation(city)}
                            />
                          </Form>
                          <Button 
                            variant="primary" 
                            className="mt-2"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleCityClick(city);
                            }}
                          >
                            View Details
                          </Button>
                        </Card.Body>
                      </Card>
                    </div>
                    );
                    })}
                </div>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Centers List view (drill-down) */}
      {currentView === 'centers' && (
        <Row className="mb-4">
          <Col>
            <Card>
              <Card.Header>
                <h2>CT Scan Centers in {selectedCity} ({getCityCenters(selectedCity).length} found)</h2>
              </Card.Header>
              <Card.Body>
                <Table striped bordered hover responsive>
                  <thead>
                    <tr>
                      <th>#</th>
                      <th 
                        onClick={() => requestSort('center_name')}
                        style={{ cursor: 'pointer' }}
                      >
                        Center Name
                        {sortConfig.key === 'center_name' && (
                          <span>{sortConfig.direction === 'asc' ? ' ↑' : ' ↓'}</span>
                        )}
                      </th>
                      <th
                        onClick={() => requestSort('city')}
                        style={{ cursor: 'pointer' }}
                      >
                        City
                        {sortConfig.key === 'city' && (
                          <span>{sortConfig.direction === 'asc' ? ' ↑' : ' ↓'}</span>
                        )}
                      </th>
                      <th 
                        onClick={() => requestSort('address')}
                        style={{ cursor: 'pointer' }}
                      >
                        Address
                        {sortConfig.key === 'address' && (
                          <span>{sortConfig.direction === 'asc' ? ' ↑' : ' ↓'}</span>
                        )}
                      </th>
                      <th 
                        onClick={() => requestSort('contact_details')}
                        style={{ cursor: 'pointer' }}
                      >
                        Contact
                        {sortConfig.key === 'contact_details' && (
                          <span>{sortConfig.direction === 'asc' ? ' ↑' : ' ↓'}</span>
                        )}
                      </th>
                      <th 
                        onClick={() => requestSort('google_maps_link')}
                        style={{ cursor: 'pointer' }}
                      >
                        Maps
                        {sortConfig.key === 'google_maps_link' && (
                          <span>{sortConfig.direction === 'asc' ? ' ↑' : ' ↓'}</span>
                        )}
                      </th>
                      <th>Notes</th>
                      <th>Validated</th>
                      <th>Qualified</th>
                      <th>Action</th>
                      <th>
                        <Form.Check
                          type="checkbox"
                          onChange={(e) => {
                            if (e.target.checked) {
                              const allIds = getCityCenters(selectedCity).map(center => center.id);
                              setSelectedForDeletion(new Set(allIds));
                            } else {
                              setSelectedForDeletion(new Set());
                            }
                          }}
                          checked={getCityCenters(selectedCity).length > 0 && 
                            getCityCenters(selectedCity).every(center => 
                              selectedForDeletion.has(center.id))}
                        />
                        Delete
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {getCityCenters(selectedCity).map((center) => {
                      const isEditing = editingCenterId === center.id;
                      const draftNote = noteDrafts[center.id] ?? center.notes ?? '';
                      const originalNote = center.notes || '';
                      const hasUnsavedNote = draftNote.trim() !== originalNote.trim();
                      const isSavingNote = noteSaving[center.id];

                      return (
                        <tr key={center.id}>
                          <td>{center.id}</td>
                          <td>
                            {isEditing ? (
                              <Form.Control
                                value={editFormData?.center_name ?? ''}
                                onChange={(e) => handleEditFieldChange('center_name', e.target.value)}
                              />
                            ) : (
                              center.center_name
                            )}
                          </td>
                          <td>
                            {isEditing ? (
                              <Form.Control
                                value={editFormData?.city ?? ''}
                                onChange={(e) => handleEditFieldChange('city', e.target.value)}
                              />
                            ) : (
                              center.city
                            )}
                          </td>
                          <td>
                            {isEditing ? (
                              <Form.Control
                                as="textarea"
                                rows={3}
                                value={editFormData?.address ?? ''}
                                onChange={(e) => handleEditFieldChange('address', e.target.value)}
                              />
                            ) : (
                              center.address
                            )}
                          </td>
                          <td>
                            {isEditing ? (
                              <Form.Control
                                as="textarea"
                                rows={2}
                                value={editFormData?.contact_details ?? ''}
                                onChange={(e) => handleEditFieldChange('contact_details', e.target.value)}
                              />
                            ) : (
                              center.contact_details && center.contact_details.trim() !== '' && center.contact_details !== 'Not provided in text' && center.contact_details !== 'Information not available.' && center.contact_details !== 'No phone number available.'
                                ? center.contact_details
                                : <span className="text-danger">No contact info</span>
                            )}
                          </td>
                          <td>
                            {isEditing ? (
                              <Form.Control
                                value={editFormData?.google_maps_link ?? ''}
                                onChange={(e) => handleEditFieldChange('google_maps_link', e.target.value)}
                                placeholder="https://"
                              />
                            ) : (
                              center.google_maps_link ? (
                                <a href={center.google_maps_link} target="_blank" rel="noopener noreferrer">
                                  View Map
                                </a>
                              ) : (
                                <span className="text-muted">No map link</span>
                              )
                            )}
                          </td>
                          <td>
                            {isEditing ? (
                              <Form.Control
                                as="textarea"
                                rows={2}
                                value={editFormData?.notes ?? ''}
                                onChange={(e) => handleEditFieldChange('notes', e.target.value)}
                                placeholder="Add notes for this center"
                              />
                            ) : (
                              <>
                                <Form.Control
                                  as="textarea"
                                  rows={2}
                                  value={draftNote}
                                  onChange={(e) => handleNoteChange(center.id, e.target.value)}
                                  placeholder="Add notes for this center"
                                />
                                <div className="mt-2 d-flex align-items-center">
                                  <Button
                                    variant="success"
                                    size="sm"
                                    disabled={isSavingNote || !hasUnsavedNote}
                                    onClick={() => handleSaveNote(center)}
                                  >
                                    {isSavingNote ? 'Saving...' : 'Save'}
                                  </Button>
                                  {hasUnsavedNote && !isSavingNote && (
                                    <small className="text-muted ms-2">Unsaved changes</small>
                                  )}
                                </div>
                              </>
                            )}
                          </td>
                          <td className="text-center">
                            {isEditing ? (
                              <Form.Check
                                type="checkbox"
                                checked={editFormData?.validated ?? false}
                                onChange={(e) => handleEditFieldChange('validated', e.target.checked)}
                              />
                            ) : (
                              <Form.Check
                                type="checkbox"
                                checked={center.validated}
                                onChange={(e) => handleValidationToggle(center.id, e.target.checked)}
                              />
                            )}
                          </td>
                          <td className="text-center">
                            {isEditing ? (
                              <Form.Check
                                type="checkbox"
                                checked={editFormData?.qualified ?? false}
                                onChange={(e) => handleEditFieldChange('qualified', e.target.checked)}
                              />
                            ) : (
                              <Form.Check
                                type="checkbox"
                                checked={center.qualified}
                                onChange={(e) => handleQualificationToggle(center.id, e.target.checked)}
                              />
                            )}
                          </td>
                          <td>
                            {isEditing ? (
                              <>
                                <Button
                                  variant="success"
                                  size="sm"
                                  className="me-2"
                                  onClick={handleSaveEdit}
                                >
                                  Save
                                </Button>
                                <Button
                                  variant="secondary"
                                  size="sm"
                                  onClick={handleCancelEdit}
                                >
                                  Cancel
                                </Button>
                              </>
                            ) : (
                              <>
                                <Button
                                  variant="outline-primary"
                                  size="sm"
                                  className="me-2"
                                  onClick={() => handleEditClick(center)}
                                >
                                  Edit
                                </Button>
                              </>
                            )}
                          </td>
                          <td>
                            {isEditing ? (
                              <Form.Check
                                type="checkbox"
                                checked={selectedForDeletion.has(center.id)}
                                disabled
                              />
                            ) : (
                              <Form.Check
                                type="checkbox"
                                checked={selectedForDeletion.has(center.id)}
                                onChange={(e) => {
                                  const newSelected = new Set(selectedForDeletion);
                                  if (e.target.checked) {
                                    newSelected.add(center.id);
                                  } else {
                                    newSelected.delete(center.id);
                                  }
                                  setSelectedForDeletion(newSelected);
                                }}
                              />
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </Table>
              </Card.Body>
              <Card.Footer>
                <Button 
                  variant="danger" 
                  onClick={() => {
                    if (selectedForDeletion.size > 0) {
                      setShowDeleteModal(true);
                    } else {
                      alert('Please select at least one record to delete.');
                    }
                  }}
                  disabled={selectedForDeletion.size === 0}
                >
                  Delete Marked Records ({selectedForDeletion.size})
                </Button>
              </Card.Footer>
            </Card>
          </Col>
        </Row>
      )}

      {/* Upload Card - show in both views */}
      <Row className="mb-4">
        <Col md={4}>
          <Card>
            <Card.Header>
              <h2>Upload New Data</h2>
            </Card.Header>
            <Card.Body>
              <Form>
                <Form.Group>
                  <Form.Control type="file" onChange={handleFileChange} accept=".csv" />
                </Form.Group>
                <Button variant="primary" onClick={handleFileUpload} className="mt-2 me-2">
                  Upload CSV
                </Button>
                <Button variant="danger" onClick={handleRemoveDuplicates} className="mt-2">
                  Remove Duplicates
                </Button>
              </Form>
            </Card.Body>
          </Card>
          
          {/* City Statistics Card - show after upload section */}
          {cityStats && (
            <Card className="mt-3">
              <Card.Header>
                <h2>Uploaded Data Summary</h2>
              </Card.Header>
              <Card.Body>
                <Row>
                  <Col md={6}>
                    <Card className="text-center bg-primary text-white">
                      <Card.Body>
                        <Card.Title>{cityStats.total_centers}</Card.Title>
                        <Card.Text>Total Centers</Card.Text>
                      </Card.Body>
                    </Card>
                  </Col>
                  <Col md={6}>
                    <Card className="text-center bg-success text-white">
                      <Card.Body>
                        <Card.Title>{cityStats.cities_count}</Card.Title>
                        <Card.Text>Cities Covered</Card.Text>
                      </Card.Body>
                    </Card>
                  </Col>
                </Row>
                
                <h4 className="mt-3">Top Cities by Center Count:</h4>
                <ul>
                  {cityStats.city_distribution
                    .sort((a, b) => b.count - a.count)
                    .slice(0, 10)
                    .map((cityData) => (
                      <li key={cityData.city}>
                        <strong>{cityData.city}</strong>: {cityData.count} centers
                      </li>
                    ))}
                </ul>
                
                <Button variant="outline-primary" onClick={fetchCityStats} className="mt-2">
                  Refresh Statistics
                </Button>
              </Card.Body>
            </Card>
          )}
        </Col>
      </Row>
      
      {/* Delete Confirmation Modal */}
      <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Confirm Deletion</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p>Are you sure you want to delete the following {selectedForDeletion.size} records?</p>
          <div style={{ maxHeight: '300px', overflowY: 'auto', border: '1px solid #ccc', padding: '10px' }}>
            <Table striped bordered hover size="sm">
              <thead>
                <tr>
                  <th>Center Name</th>
                  <th>City</th>
                  <th>Address</th>
                </tr>
              </thead>
              <tbody>
                {Array.from(selectedForDeletion).map(id => {
                  const center = centers.find(c => c.id === id);
                  return center ? (
                    <tr key={center.id}>
                      <td>{center.center_name}</td>
                      <td>{center.city}</td>
                      <td>{center.address.substring(0, 50)}{center.address.length > 50 ? '...' : ''}</td>
                    </tr>
                  ) : null;
                })}
              </tbody>
            </Table>
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
            Cancel
          </Button>
          <Button 
            variant="danger" 
            onClick={async () => {
              try {
                // Delete all selected records
                for (const id of selectedForDeletion) {
                  await axios.delete(`${API_BASE_URL}/api/centers/${id}`);
                }
                
                alert(`Successfully deleted ${selectedForDeletion.size} records`);
                
                // Clear selection and close modal
                setSelectedForDeletion(new Set());
                setShowDeleteModal(false);
                
                // Refresh the data
                fetchCenters();
                fetchCityStats();
              } catch (error) {
                console.error('Error deleting centers:', error);
                alert('Error deleting records. Please try again.');
              }
            }}
          >
            Confirm Delete
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
}

export default App;
