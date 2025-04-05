import { Box, Typography, Button } from "@material-ui/core";
import * as React from "react";
import { useDispatch, useSelector } from "react-redux";
import AccordionSentence from "../../sharedComponents/Sentence/sentence";
import { multiLabelData } from "../../actions/annotation_actions";
import {
  changeSetting,
  updateNegativeElementLabel,
} from "../../actions/Dataslice";
import { fetchCombinedPatterns, fetchPatterns } from "../../actions/pattern_actions";
import { Chip } from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import { lighten } from "@material-ui/core";
import { base_url } from "../../assets/base_url";

import Fab from "@mui/material/Fab";
import LabelSelector from "../../sharedComponents/LabelSelector/labelselector";

import SentenceLight from "../../sharedComponents/Sentence/sentenceLight";
import { Stack } from "@mui/material";

export default function SentenceViewer({
  getSelection,
  hovering,
  setHovering,
  setScrollPosition,
  setOpenSideBar,
  focusedId,
  setFocusedId,
  setPopoverAnchor,
  setPopoverContent,
  setActiveSentenceGroup,
}) {
  const workspace = useSelector((state) => state.workspace);
  const dispatch = useDispatch();

  const [positiveIds, setPositiveIds] = React.useState({});
  const [labelSelectorAnchor, setLabelSelectorAnchor] = React.useState(null);
  const [batchLabeling, setBatchLabeling] = React.useState(null);
  const [currentBatch, setCurrentBatch] = React.useState(0);
  const [viewMode, setViewMode] = React.useState('default');
  const BATCH_SIZE = 10;

  React.useEffect(() => {
    if (workspace.loadingCombinedPatterns || workspace.loadingPatterns) {
      setHovering(null);
    }
  }, [workspace.loadingCombinedPatterns, workspace.loadingPatterns]);

  const handleAddToPos = (elem) => {
    console.log("Adding to positiveIds:", elem);
    let ps = { ...positiveIds };
    ps[elem.element_id] = elem.label;
    console.log("Updated positiveIds:", ps);
    setPositiveIds(ps);
  };

  const handleBatchLabeling = () => {
    console.log("==========================================");
    console.log("Starting batch labeling process");
    console.log("Current batch:", currentBatch);
    console.log("Current state:", workspace);
    setHovering(null);

    const currentBatchSentences = getCurrentBatch(workspace.groups.flat());
    const labeledCount = getCurrentBatchLabeledCount(workspace.groups.flat());

    console.log("Current batch sentences:", currentBatchSentences);
    console.log("Labeled count:", labeledCount, "of", BATCH_SIZE);

    if (labeledCount < BATCH_SIZE) {
      console.log("Not all samples are labeled yet, returning early");
      console.log("==========================================");
      return;
    }

    // Skip pattern generation and directly advance to next batch
    console.log("Advancing to next batch");
    
    // First fetch predictions for current batch to ensure everything is processed
    console.log("Fetching predictions for current batch:", currentBatch);
    
    const fetchCurrentBatch = dispatch(fetchCombinedPatterns({ currentBatch, batchSize: BATCH_SIZE }));
    
    console.log("Promise for current batch:", fetchCurrentBatch);
    console.log("Adding then handler to promise");
    
    fetchCurrentBatch.then((response) => {
      console.log("Current batch response received:", response);
      
      // Advance to next batch and fetch predictions for it
      const allSentences = workspace.groups.flat();
      console.log("Total sentences:", allSentences.length);
      console.log("Next batch would start at:", (currentBatch + 1) * BATCH_SIZE);
      
      if ((currentBatch + 1) * BATCH_SIZE < allSentences.length) {
        const nextBatch = currentBatch + 1;
        console.log(`Moving to batch ${nextBatch}`);
        
        console.log("Setting currentBatch to:", nextBatch);
        setCurrentBatch(nextBatch);
        
        console.log("Clearing positiveIds");
        setPositiveIds({});
        
        // Special handling for batch 1 - try a different approach
        if (nextBatch === 1) {
          console.log("SPECIAL HANDLING FOR BATCH 1");
          console.log("This is where we had issues before - trying a different approach");
          
          // Try a direct fetch 
          try {
            console.log("Making a direct fetch request for batch 1");
            
            const userStr = window.localStorage.getItem("user");
            const user = userStr ? userStr.replaceAll('"', "") : "unknown"; 
            // Use the same base URL as the rest of the app
            const directUrl = `${base_url}/annotations?batch=1&batch_size=${BATCH_SIZE}`;
            
            console.log(`Direct fetch URL: ${directUrl}`);
            console.log(`User: ${user}`);
            
            // Make a direct fetch request (this bypasses Redux and AbortController)
            fetch(directUrl, {
              method: "GET",
              headers: {
                "Content-Type": "application/json",
                "credentials": "include",
                "annotuser": user
              }
            })
            .then(response => {
              console.log("Direct fetch response received:", response);
              if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
              }
              return response.json();
            })
            .then(data => {
              console.log("Direct fetch data received:", data);
            })
            .catch(error => {
              console.error("Direct fetch error:", error);
            });
          } catch (error) {
            console.error("Error in direct fetch attempt:", error);
          }
        }
        
        // Fetch predictions for the new batch using dispatch
        console.log("Dispatching fetchCombinedPatterns for next batch:", nextBatch);
        const fetchNextBatch = dispatch(fetchCombinedPatterns({ currentBatch: nextBatch, batchSize: BATCH_SIZE }));
        
        console.log("Promise for next batch:", fetchNextBatch);
        
        fetchNextBatch
          .then((response) => {
            console.log("Next batch data fetched successfully:", response);
            console.log("==========================================");
          })
          .catch((error) => {
            console.error("Error fetching next batch:", error);
            console.error("Error details:", JSON.stringify(error));
            console.log("==========================================");
          });
      } else {
        console.log("No more batches available");
        console.log("==========================================");
      }
      console.log("Advanced to next batch");
    })
    .catch((error) => {
      console.error("Error processing current batch:", error);
      console.error("Error details:", JSON.stringify(error));
      console.log("==========================================");
    });
    
    console.log("handleBatchLabeling completed, waiting for promises");
  };

  const getCurrentBatch = (groups) => {
    const start = currentBatch * BATCH_SIZE;
    const end = start + BATCH_SIZE;
    return groups.slice(start, end);
  };

  const getCurrentBatchLabeledCount = (groups) => {
    const currentBatchSentences = getCurrentBatch(groups);
    let count = 0;
    
    currentBatchSentences.forEach(id => {
      // Check positive labels
      if (workspace.element_to_label[id] && 
          workspace.element_to_label[id].includes(workspace.selectedTheme)) {
        count++;
      }
      // Check negative labels
      if (workspace.negative_element_to_label[id] && 
          workspace.negative_element_to_label[id].includes(workspace.selectedTheme)) {
        count++;
      }
    });
    
    return count;
  };

  const handleNextBatch = () => {
    console.log("========== NEXT BATCH HANDLER ==========");
    const allSentences = workspace.groups.flat();
    const nextBatch = currentBatch + 1;
    
    if (nextBatch * BATCH_SIZE < allSentences.length) {
      console.log(`Moving to batch ${nextBatch} directly`);
      
      // Update UI state first
      setCurrentBatch(nextBatch);
      setPositiveIds({});
      
      // Then fetch the data
      console.log(`Fetching data for batch ${nextBatch}`);
      dispatch(fetchCombinedPatterns({ 
        currentBatch: nextBatch, 
        batchSize: BATCH_SIZE 
      }))
      .then(response => {
        console.log("Batch data fetched successfully:", response);
      })
      .catch(error => {
        console.error("Error fetching batch data:", error);
      });
    } else {
      console.log("No more batches available");
    }
    console.log("========== END NEXT BATCH HANDLER ==========");
  };

  const handlePrevBatch = () => {
    if (currentBatch > 0) {
      setCurrentBatch(prev => prev - 1);
      setPositiveIds({});
    }
  };

  const renderDefaultView = () => {
    const allSentences = workspace.groups.flat();
    const currentBatchSentences = getCurrentBatch(allSentences);
    const labeledCount = getCurrentBatchLabeledCount(allSentences);
    
    return (
      <Stack mb={5}>
        <Typography variant="h6" align="center" gutterBottom>
          Batch {currentBatch + 1} of {Math.ceil(allSentences.length / BATCH_SIZE)}
        </Typography>
        <Typography variant="subtitle1" align="center" gutterBottom>
          Labeled: {labeledCount} of {BATCH_SIZE} samples
        </Typography>
        {currentBatchSentences.map((elementId, index) => (
          <AccordionSentence
            marginLeft={10}
            seeMore={setOpenSideBar}
            index={index}
            positiveIds={positiveIds}
            setPositiveIds={handleAddToPos}
            explanation={
              hovering && workspace.explanation
                ? workspace.explanation[hovering][elementId]
                : null
            }
            hovering={hovering}
            score={workspace.elements[elementId].score}
            key={`sent_default_${elementId}`}
            elementId={elementId}
            example={workspace.elements[elementId].example}
            focused={focusedId == elementId}
            setFocusedId={setFocusedId}
            theme={workspace.selectedTheme}
            annotationPerRetrain={workspace.annotationPerRetrain}
            getSelection={getSelection}
            retrain={handleBatchLabeling}
            setPopoverAnchor={setPopoverAnchor}
            setPopoverContent={setPopoverContent}
            setAnchorEl={setLabelSelectorAnchor}
            showPrediction={true}
          />
        ))}
        <Stack direction="row" spacing={2} justifyContent="center" mt={2}>
          <Button 
            variant="contained" 
            onClick={handlePrevBatch}
            disabled={currentBatch === 0}
          >
            Previous
          </Button>
          <Button 
            variant="contained" 
            onClick={() => {
              console.log("NEXT BATCH button clicked");
              handleNextBatch();
            }}
            disabled={getCurrentBatchLabeledCount(workspace.groups.flat()) < BATCH_SIZE}
            color="primary"
          >
            Next Batch ({getCurrentBatchLabeledCount(workspace.groups.flat())}/{BATCH_SIZE})
          </Button>
        </Stack>
      </Stack>
    );
  };

  const renderGroupedView = () => {
    return workspace.groups.map((groups, groupIndex) => {
      const currentBatchSentences = getCurrentBatch(groups);
      const labeledCount = getCurrentBatchLabeledCount(groups);
      
      return (
        <Stack
          mb={5}
          sx={{
            ...(workspace.groups.length > 1 && {
              border: "solid 8px #4f4a50",
              borderRadius: "10px",
            }),
          }}
        >
          <Typography variant="h6" align="center" gutterBottom>
            Batch {currentBatch + 1} of {Math.ceil(groups.length / BATCH_SIZE)}
          </Typography>
          <Typography variant="subtitle1" align="center" gutterBottom>
            Labeled: {labeledCount} of {BATCH_SIZE} samples
          </Typography>
          {currentBatchSentences.map((elementId, index) => (
            <AccordionSentence
              groupIndex={groupIndex}
              marginLeft={10}
              seeMore={setOpenSideBar}
              index={index}
              positiveIds={positiveIds}
              setPositiveIds={handleAddToPos}
              explanation={
                hovering && workspace.explanation
                  ? workspace.explanation[hovering][elementId]
                  : null
              }
              hovering={hovering}
              score={workspace.elements[elementId].score}
              key={`sent_grouped_${elementId}`}
              elementId={elementId}
              example={workspace.elements[elementId].example}
              focused={focusedId == elementId}
              setFocusedId={setFocusedId}
              theme={workspace.selectedTheme}
              annotationPerRetrain={workspace.annotationPerRetrain}
              getSelection={getSelection}
              retrain={handleBatchLabeling}
              setPopoverAnchor={setPopoverAnchor}
              setPopoverContent={setPopoverContent}
              setAnchorEl={setLabelSelectorAnchor}
              showPrediction={true}
            />
          ))}
          <Stack direction="row" spacing={2} justifyContent="center" mt={2}>
            <Button 
              variant="contained" 
              onClick={handlePrevBatch}
              disabled={currentBatch === 0}
            >
              Previous
            </Button>
            <Button 
              variant="contained" 
              onClick={handleNextBatch}
              disabled={(currentBatch + 1) * BATCH_SIZE >= groups.length}
            >
              Next
            </Button>
          </Stack>
        </Stack>
      );
    });
  };

  return (
    <Box
      style={{
        maxHeight: "100%",
        maxWidth: "50vw",
        minWidth: "50vw",
        overflow: "auto",
        marginLeft: "10px",
      }}
      onScroll={(event) => {
        setScrollPosition(event.target.scrollTop / event.target.scrollHeight);
      }}
    >
      <LabelSelector
        anchorEl={labelSelectorAnchor}
        setAnchorEl={setLabelSelectorAnchor}
        elementId={focusedId}
        groupLabeling={batchLabeling}
        setBatchLabeling={setBatchLabeling}
      />

      {!hovering && (
        <>
          <Stack direction="row" spacing={2} justifyContent="center" mb={2}>
            <Button 
              variant={viewMode === 'default' ? 'contained' : 'outlined'}
              onClick={() => setViewMode('default')}
            >
              Default View
            </Button>
            <Button 
              variant={viewMode === 'grouped' ? 'contained' : 'outlined'}
              onClick={() => setViewMode('grouped')}
            >
              Grouped View
            </Button>
          </Stack>
          {viewMode === 'default' ? renderDefaultView() : renderGroupedView()}
        </>
      )}

      {hovering &&
        workspace.explanation &&
        workspace.groups &&
        workspace.groups.map((groups, groupIndex) => {
          const currentBatchSentences = getCurrentBatch(groups);
          const labeledCount = getCurrentBatchLabeledCount(groups);
          
          return (
            <Stack
              mb={10}
              sx={{ backgroundColor: "#cececece", border: "solid 3px #cececece" }}
            >
              <Typography variant="h6" align="center" gutterBottom>
                Batch {currentBatch + 1} of {Math.ceil(groups.length / BATCH_SIZE)}
              </Typography>
              <Typography variant="subtitle1" align="center" gutterBottom>
                Labeled: {labeledCount} of {BATCH_SIZE} samples
              </Typography>
              {currentBatchSentences.map((elementId, index) => (
                <SentenceLight
                  show={
                    workspace.explanation[hovering] &&
                    workspace.explanation[hovering][elementId]
                  }
                  highlight={
                    workspace.explanation[hovering] &&
                    workspace.explanation[hovering][elementId]
                  }
                  color={
                    workspace.color_code[workspace.selectedTheme]
                      ? lighten(
                          workspace.color_code[workspace.selectedTheme],
                          0.5
                        )
                      : "none"
                  }
                  element={workspace.elements[elementId]}
                  handleBatchLabel={(element_id, label) =>
                    handleAddToPos({ element_id, label })
                  }
                  highlightAsList={true}
                  sentence={workspace.elements[elementId].example}
                  key={`lightsent_hovering_${elementId}`}
                />
              ))}
              <Stack direction="row" spacing={2} justifyContent="center" mt={2}>
                <Button 
                  variant="contained" 
                  onClick={handlePrevBatch}
                  disabled={currentBatch === 0}
                >
                  Previous
                </Button>
                <Button 
                  variant="contained" 
                  onClick={handleNextBatch}
                  disabled={(currentBatch + 1) * BATCH_SIZE >= groups.length}
                >
                  Next
                </Button>
              </Stack>
            </Stack>
          );
        })}

      {hovering && Object.keys(positiveIds).length > 0 && (
        <Fab
          sx={{ position: "sticky", bottom: "50px", marginLeft: "20px" }}
          color={"primary"}
          variant="extended"
          onClick={handleBatchLabeling}
        >
          Done
        </Fab>
      )}
    </Box>
  );
}
