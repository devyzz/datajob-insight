document.addEventListener('DOMContentLoaded', () => {    
    // 그리드를 표시할 HTML 요소 선택
    const gridDiv = document.querySelector('#jobGrid');
    if (!gridDiv) {
        console.error('AG Grid의 div 요소를 찾을 수 없습니다. HTML의 ID가 "jobGrid"인지 확인하세요.');
        return; // gridDiv가 없으면 더 이상 진행하지 않음
    }

    const columnDefs = [
        // --- ID 컬럼들 (기본적으로 숨김 처리, 필요시 주석 해제하여 사용) ---
        // { headerName: "공고 ID", field: "posting_id", width: 100 },
        // { headerName: "회사 ID", field: "company_id", width: 100 },
        // { headerName: "플랫폼 ID", field: "platform_id", width: 120 },
        // --- 주요 정보 컬럼들 ---
        { 
            headerName: "ID", 
            field: "company_id", // Tip: 실제 회사명을 보려면 백엔드에서 company 테이블과 JOIN하여 회사명(예: company_name)을 내려줘야 합니다.
            sortable: true, 
            filter: 'agNumberColumnFilter', // 숫자 필터 사용
            width: 120 
        },
        { 
            headerName: "공고제목", 
            field: "title", 
            sortable: true, 
            filter: 'agTextColumnFilter', // 텍스트 필터 사용
            flex: 3 // 가장 넓은 영역을 차지하도록 설정
        },
        { 
            headerName: "포지션", 
            field: "position", 
            sortable: true, 
            filter: 'agTextColumnFilter',
            flex: 1.5 
        },
        { 
            headerName: "근무지역", 
            field: "location", // 'location_name'이 아닌 모델에 정의된 'location' 사용
            sortable: true, 
            filter: 'agTextColumnFilter',
            flex: 1.5 
        },
        { 
            headerName: "근무형태", 
            field: "job_type", 
            sortable: true, 
            filter: 'agTextColumnFilter',
            width: 120 
        },

        // --- 상세 조건 컬럼들 ---
        { 
            headerName: "경력", 
            field: "experience_min", 
            // valueGetter를 사용해 min과 max를 합쳐서 보여주는 예시
            valueGetter: params => {
                const min = params.data.experience_min || '';
                const max = params.data.experience_max || '';
                if (min === max || !max) return min;
                return `${min} ~ ${max}`;
            },
            sortable: true, 
            filter: 'agTextColumnFilter',
            width: 120 
        },
        { 
            headerName: "학력", 
            field: "education", 
            sortable: true, 
            filter: 'agTextColumnFilter',
            width: 120 
        },
        { 
            headerName: "기술스택", 
            field: "tech_stack", 
            sortable: false, // 기술스택은 정렬의 의미가 크지 않으므로 false 처리
            filter: 'agTextColumnFilter',
            flex: 2 
        },
        
        // --- 날짜 및 기타 정보 ---
        { 
            headerName: "마감일", 
            field: "apply_end_date", 
            sortable: true, 
            filter: 'agTextColumnFilter',
            width: 130 
        },
        { 
            headerName: "수집일", 
            field: "crawled_at", 
            sortable: true, 
            filter: 'agDateColumnFilter',
            // valueFormatter를 사용해 날짜 형식을 'YYYY-MM-DD'로 깔끔하게 표시
            valueFormatter: params => params.value ? params.value.split('T')[0] : '',
            width: 130 
        },
        {
            headerName: "URL",
            field: "url", // 'url_link'가 아닌 모델에 정의된 'url' 사용
            sortable: false,
            filter: false,
            width: 80,
            // cellRenderer를 사용해 실제 클릭 가능한 HTML 링크로 만듭니다.
            cellRenderer: params => { 
                if (params.value) {
                    // target="_blank"는 새 탭에서 링크를 열도록 합니다.
                    return `<a href="${params.value}" target="_blank" rel="noopener noreferrer">보기</a>`;
                }
                return '';
            }
        },
    ];

    // 그리드 옵션
    const gridOptions = {
        columnDefs: columnDefs,
        rowData: null, // 초기 데이터는 API 호출 후 설정
        pagination: true,
        paginationPageSize: 15, // 한 페이지에 보여줄 행 수
        paginationPageSizeSelector:[10, 15, 20, 50],
        domLayout: 'autoHeight', // 그리드 높이를 내용에 맞게 자동 조절
        defaultColDef: {
            sortable: true,
            filter: true,
            resizable: true,
        },
        onGridReady: function(params) {
            // API에서 데이터 가져와서 그리드에 채우기
            fetch('/jobs/data?limit=500')
                .then(response => {
                    console.log('Fetch 응답 받음, 상태:', response.status); // << 추가
                    if (!response.ok) {
                        // 서버 응답이 정상이 아닐 때 (예: 404, 500) 오류를 발생시켜 catch 블록으로 넘김
                        return response.text().then(text => { 
                            throw new Error('Network response was not ok: ' + response.status + ' ' + response.statusText + '. Server says: ' + text);
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('API로부터 데이터 받음 (첫 번째 항목):', data && data.length > 0 ? data[0] : '데이터 없음 또는 빈 배열'); // << 추가
                    if (params.api) {
                        params.api.setRowData(data);
                        console.log('데이터가 그리드에 설정됨'); // << 추가
                    } else {
                        console.error('Grid API를 사용할 수 없습니다 (onGridReady 내부).');
                    }
                })
                .catch(error => {
                    console.error('데이터를 가져오거나 파싱하는 중 오류 발생:', error);
                    if (gridDiv) {
                        gridDiv.innerHTML = '<p>데이터를 불러오는 데 실패했습니다. 브라우저 콘솔을 확인해주세요. 오류: ' + error.message + '</p>';
                    }
                });
        }
    };

    // AG Grid 생성
    try {
        console.log('AG Grid 인스턴스 생성 시도...'); // << 추가
        // agGrid 라이브러리가 로드되었는지 기본적인 확인
        if (typeof agGrid === 'undefined' || typeof agGrid.Grid !== 'function') {
            console.error('AG Grid 라이브러리(agGrid.Grid)가 로드되지 않았거나 사용할 수 없습니다.');
            if(gridDiv) gridDiv.innerHTML = '<p>AG Grid 라이브러리 로드 실패. HTML의 스크립트 태그를 확인하세요.</p>';
            return;
        }
        new agGrid.Grid(gridDiv, gridOptions);
    } catch (e) {
        console.error('AG Grid 생성 중 예외 발생:', e);
        if (gridDiv) {
            gridDiv.innerHTML = '<p>AG Grid 초기화 중 오류 발생. 콘솔을 확인해주세요.</p>';
        }
    }
});